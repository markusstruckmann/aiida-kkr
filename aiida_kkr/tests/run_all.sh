#!/usr/bin/env bash
export AIIDA_PATH='.';
mkdir -p '.aiida';

# control test coverage by setting the envoronment variables
# SKIP_NOWORK   to run only workflow tests
# RUN_VORONOI   to run tests using voronoi
# RUN_KKRHOST   to run tests using KKRhost
# RUN_KKRIMP    to run tests using KKRimp
# RUN_ALL       to run all tests
# if the environment variable is unset or the empty string then the corresponding tests will be ignored 

usage(){
  echo "$0 usage:" && grep " .)\ #" $0;
  echo
  echo "Default behavior is to run only tests that do not require running an actual calculation (i.e. skip workflow tests)."
  echo "Additional settings with the environment variables (set to something or unset to remove setting):";
  echo "  'RUN_ALL': run all tests";
  echo "  'SKIP_NOWORK': skip workflow tests";
  echo "  'RUN_VORONOI': run voronoi tests";
  echo "  'RUN_KKRHOST': run kkrhost tests";
  echo "  'RUN_KKRIMP': run kkrimp tests";
  echo
  exit 0;
}

addopt=""
while getopts vh option; do
  case $option in
    v) # Add verbosity flags '-sv' to pytest run
       addopt=" -sv " && echo "Found -v flag: adding option '$addopt' to pytest execution" ;;
    h) # Display help
       usage
  esac
done


# print settings before starting the tests
echo "Test settings"
echo "============="
if [[ ! -z "$RUN_ALL" ]]; then
  echo "Running all test (needs all KKR executables, set by 'RUN_ALL' env)"
else
  if [[ -z "$SKIP_NOWORK" ]]; then
    echo "run non-workflow tests (prevent this with 'SKIP_NOWORK' env)"
  else
    echo "skip non-workflow tests (unset 'SKIP_NOWORK' env to activate this)"
  fi
  if [[ ! -z "$RUN_VORONOI" ]]; then
    echo "run workflows using voronoi code (unset 'RUN_VORONOI' env to prevent this)"
  else
    echo "skip workflows tests using voronoi (set 'RUN_VORONOI' env to activate this)"
  fi
  if [[ ! -z "$RUN_KKRHOST" ]]; then
    echo "run workflows using KKRhost code (unset 'RUN_KKRHOST' env to prevent this)"
  else
    echo "skip workflows tests using KKRhost (set 'RUN_KKRHOST' env to activate this)"
  fi
  if [[ ! -z "$RUN_KKRIMP" ]]; then
    echo "run workflows using KKRimp code (unset 'RUN_KKRIMP' env to prevent this)"
  else
    echo "skip workflows tests using KKRimp (set 'RUN_KKRIMP' env to activate this)"
  fi
  if [[ ! -z "$NO_RMQ" ]]; then
    echo "do not run workflows and workfuntions that need rabbitMQ (unset 'NO_RMQ' env to prevent this)"
  else
    echo "run workflows and workfunctions also with rabbitMQ (set 'NO_RMQ' env to deactivate this)"
  fi
fi
echo "============="
echo

# Now run tests

if [[ ! -z "$RUN_ALL" ]]; then
  echo "run all tests (first workflows then non-workflows tools etc)"
  pytest --cov-report=term-missing --cov=aiida_kkr --ignore=jukkr -k workflows # run workflows first
  pytest --cov-report=term-missing --cov=aiida_kkr --cov-append --ignore=jukkr --ignore=workflows --mpl -p no:warnings $addopt # then run non-workflow tests
else
  # tests without running actual calculations
  if [[ -z "$SKIP_NOWORK" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run non-workflow tests"
    pytest --cov-report=term-missing --cov=aiida_kkr --ignore=workflows --ignore=jukkr --mpl -p no:warnings $addopt
  else
    # skip things that need rabbitMQ
    if [[ -z "$SKIP_NOWORK" ]] && [[ ! -z "$NO_RMQ" ]]; then
      echo "run non-workflow tests"
      pytest --cov-report=term-missing --cov=aiida_kkr --ignore=workflows --ignore=jukkr --ignore=calculations --ignore=test_common_workfunctions_with_rmq.py --ignore=test_plot_kkr.py --mpl -p no:warnings $addopt
    else
      echo "skipping tests that are not workflows"
    fi
  fi

  # test running full workflows, need compiled codes and execute them

  # tests using only voronoi

  if [[ ! -z "$RUN_VORONOI" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run vorostart workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_vorostart_workflow $addopt
  else
    echo "skipping vorostart workflow test"
  fi

  # tests using kkrhost (and voronoi)

  if [[ ! -z "$RUN_KKRHOST" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkr_dos workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_dos_workflow $addopt
  else
    echo "skipping kkr_dos workflow test"
  fi
  if [[ ! -z "$RUN_KKRHOST" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkr_gf_writeout workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_gf_writeout_workflow $addopt
  else
    echo "skipping kkr_gf_writeout workflow test"
  fi
  if [[ ! -z "$RUN_VORONOI" ]] && [[ ! -z "$RUN_KKRHOST" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkr_scf workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_scf_workflow $addopt
  else
    echo "skipping kkr_scf workflow test"
  fi
  if [[ ! -z "$RUN_VORONOI" ]] && [[ ! -z "$RUN_KKRHOST" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkr_eos workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_eos_workflow $addopt
  else
    echo "skipping kkr_eos workflow test"
  fi

  # tests using kkrimp (and kkrhost/voronoi)

  if [[ ! -z "$RUN_KKRIMP" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkrimp_scf workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_kkrimp_scf_workflow $addopt
  else
    echo "skipping kkrimp_scf workflow test"
  fi
  if [[ ! -z "$RUN_KKRIMP" ]] && [[ ! -z "$RUN_KKRHOST" ]] && [[ ! -z "$RUN_VORONOI" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkrimp_full workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_kkrimp_full_workflow $addopt
  else
    echo "skipping kkrimp_full workflow test"
  fi
  if [[ ! -z "$RUN_KKRIMP" ]] && [[ ! -z "$RUN_KKRHOST" ]] && [[ -z "$NO_RMQ" ]]; then
    echo "run kkrimp_dos workflow test"
    pytest --cov-report=term-missing --cov-append --cov=aiida_kkr --ignore=jukkr -k Test_kkrimp_dos_workflow $addopt
  else
    echo "skipping kkrimp_dos workflow test"
  fi

fi
