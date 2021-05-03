"""
Here we define the fixtures for the tests
"""

from __future__ import absolute_import
from __future__ import print_function
import pytest
import tempfile
import shutil
import pathlib
from aiida.common.hashing import make_hash
from aiida.orm import RemoteData
from aiida.manage.tests.pytest_fixtures import aiida_profile, temp_dir
import aiida_kkr


pytest_plugins = ['aiida.manage.tests.pytest_fixtures']
# test settings:

test_dir = pathlib.Path(aiida_kkr.tests.__file__).parent
data_dir = (test_dir / 'data_dir')  # TODO: get from config?

# fixtures


@pytest.fixture(scope='function', autouse=True)
def clear_database_auto(clear_database):
    """Automatically clear database in between tests."""
    pass


# need fixed aiida_localhost to have set_default_mpiprocs_per_machine set to 1
@pytest.fixture(scope='function')
def aiida_localhost_serial(temp_dir):  # pylint: disable=redefined-outer-name
    """Get an AiiDA computer for localhost.

    Usage::

      def test_1(aiida_localhost):
          name = aiida_localhost.get_name()
          # proceed to set up code or use 'aiida_local_code_factory' instead


    :return: The computer node
    :rtype: :py:class:`aiida.orm.Computer`
    """
    from aiida.orm import Computer
    from aiida.common.exceptions import NotExistent

    name = 'localhost-test'

    try:
        computer = Computer.objects.get(name=name)
    except NotExistent:
        computer = Computer(
            name=name,
            description='localhost computer set up by test manager',
            hostname=name,
            workdir=temp_dir,
            transport_type='local',
            scheduler_type='direct'
        )
        computer.store()
        computer.set_minimum_job_poll_interval(0.)
        computer.set_default_mpiprocs_per_machine(1)
        computer.configure()

    return computer



@pytest.fixture(scope='function')
def aiida_local_code_factory_prepend(aiida_localhost_serial): # pylint: disable=redefined-outer-name
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('pw.x', 'quantumespresso.pw')
          # use code for testing ...

    :return: A function get_code(executable, entry_point) that returns the Code node.
    :rtype: object
    """

    def get_code(entry_point, executable, computer=aiida_localhost_serial, prepend_text=None):
        """Get local code.
        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param executable: name of executable; will be searched for in local system PATH.
        :param computer: (local) AiiDA computer
        :return: The code node
        :rtype: :py:class:`aiida.orm.Code`
        """
        from aiida.orm import Code

        codes = Code.objects.find(filters={'label': executable})  # pylint: disable=no-member
        if codes:
            return codes[0]

        executable_path = shutil.which(executable)

        if not executable_path:
            raise ValueError('The executable "{}" was not found in the $PATH.'.format(executable))

        code = Code(
            input_plugin_name=entry_point,
            remote_computer_exec=[computer, executable_path]
        )
        code.label = executable
        if prepend_text is not None:
            code.set_prepend_text(prepend_text)
        return code.store()

    return get_code



@pytest.fixture(scope='function')
def reuse_local_code(aiida_local_code_factory_prepend):

    def _get_code(executable, exec_relpath, entrypoint, prepend_text=None, use_export_file=True):
        import os
        from aiida.tools.importexport import import_data, export
        from aiida.orm import ProcessNode, QueryBuilder, Code, load_node

        full_import_path = str(data_dir)+'/'+executable+'.tar.gz'
        # check if exported code exists and load it, otherwise create new code (will have different has due to different working directory)
        if use_export_file and pathlib.Path(full_import_path).exists():
            import_data(full_import_path, silent=True)
            codes = Code.objects.find(filters={'label': executable})  # pylint: disable=no-member
            code = codes[0]
            code.computer.configure()

        else:
            # make sure code is found in PATH
            _exe_path = (test_dir / pathlib.Path(exec_relpath)).absolute()
            print(_exe_path)
            os.environ['PATH']+=':'+str(_exe_path)
            # get code using aiida_local_code_factory fixture
            code = aiida_local_code_factory_prepend(entrypoint, executable, prepend_text=prepend_text)
            
            if use_export_file:
                #export for later reuse
                export([code], outfile=full_import_path, overwrite=True) # add export of extras automatically

        return code

    return _get_code


@pytest.fixture(scope='function')
def voronoi_local_code_import(reuse_local_code):
    """
    Create or load KKRhost code
    """
    import os
    executable = 'voronoi.exe' # name of the Voronoi executable
    exec_rel_path = 'jukkr/'   # location where it is found
    entrypoint = 'kkr.voro'    # entrypoint
    # prepend text to be added before execution
    prepend_text = """
ulimit -s hard
ln -s {}/ElementDataBase .""".format(os.path.abspath(exec_rel_path))
    voro_code = reuse_local_code(executable, exec_rel_path, entrypoint, prepend_text)
    
    return voro_code

@pytest.fixture(scope='function')
def voronoi_local_code(reuse_local_code):
    """
    Create or load KKRhost code
    """
    import os
    executable = 'voronoi.exe' # name of the Voronoi executable
    exec_rel_path = 'jukkr/'   # location where it is found
    entrypoint = 'kkr.voro'    # entrypoint
    # prepend text to be added before execution
    prepend_text = """
ulimit -s hard
ln -s {}/ElementDataBase .
source compiler-select intel""".format(os.path.abspath(exec_rel_path))
    voro_code = reuse_local_code(executable, exec_rel_path, entrypoint, prepend_text, use_export_file=False)
    
    return voro_code


@pytest.fixture(scope='function')
def kkrhost_local_code(reuse_local_code):
    """
    Create or load KKRhost code
    """
    executable = 'kkr.x' # name of the KKRhost executable
    exec_rel_path = 'jukkr/'   # location where it is found
    entrypoint = 'kkr.kkr'  # entrypoint
    # prepend text to be added before execution
    prepend_text = """
ulimit -s hard
export OMP_STACKSIZE=2G
source compiler-select intel"""
    kkrhost_code = reuse_local_code(executable, exec_rel_path, entrypoint, prepend_text, use_export_file=False)
    
    return kkrhost_code


@pytest.fixture(scope='function')
def kkrimp_local_code(reuse_local_code):
    """
    Create or load KKRimp code
    """
    executable = 'kkrflex.exe' # name of the KKRimp executable
    exec_rel_path = 'jukkr/'   # location where it is found
    entrypoint = 'kkr.kkrimp'  # entrypoint
    # prepend text to be added before execution
    prepend_text = """
ulimit -s hard
export OMP_STACKSIZE=2G
source compiler-select intel"""
    kkrimp_code = reuse_local_code(executable, exec_rel_path, entrypoint, prepend_text, use_export_file=False)
    
    return kkrimp_code

    
@pytest.fixture
def generate_remote_data():
    """Return a `RemoteData` node."""

    def _generate_remote_data(computer, remote_path, entry_point_name=None):
        """Return a `RemoteData` node which points to some dir."""
        from aiida.common.links import LinkType
        from aiida.plugins.entry_point import format_entry_point_string

        entry_point = format_entry_point_string('aiida.calculations', entry_point_name)

        remote = RemoteData(remote_path=remote_path)
        remote.computer = computer

        if entry_point_name is not None:
            creator = CalcJobNode(computer=computer, process_type=entry_point)
            creator.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
            remote.add_incoming(creator, link_type=LinkType.CREATE, link_label='remote_folder')
            creator.store()

        return remote

    return _generate_remote_data


def import_with_migration(archive_path):
    """Import aiida export file and try migration if version is incompatible"""
    from aiida.tools.importexport import (
        detect_archive_type, EXPORT_VERSION, import_data, IncompatibleArchiveVersionError
    )
    from aiida.tools.importexport.archive.migrators import get_migrator
    from aiida.common.folders import SandboxFolder
    import_kwargs = dict(extras_mode_existing='nnl', silent=True)
    try:
        imported_nodes = import_data(archive_path, **import_kwargs)
    except IncompatibleArchiveVersionError as exception:
        print('incompatible version detected for import file, trying migration')
        with SandboxFolder() as temp_folder:
            try:
                migrator = get_migrator(detect_archive_type(archive_path))(archive_path)
                archive_path = migrator.migrate(
                    EXPORT_VERSION, None, out_compression='none', work_dir=temp_folder.abspath
                )
            except Exception as exception:
                print('an exception occurred while migrating the archive', exception)
            
            print('proceeding with import of migrated archive')
            try:
                imported_nodes = import_data(archive_path, **import_kwargs)
            except Exception as exception:
                print(
                    'an exception occurred while trying to import the migrated archive', exception
                )
    return imported_nodes
