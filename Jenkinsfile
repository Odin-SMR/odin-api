@Library('molflow')

node() {
  def odinapiImage
  try {
    stages {
      stage('git') {
        checkout scm
      }
      stage('unit tests') {
        parallel python: {
          sh "./run_unittests.sh -- --runslow"
        },
        javascript: {
          sh "npm install && npm update && npm test"
        }
      }
      stage('build') {
        odinapiImage = docker.build("docker2.molflow.com/odin_redo/odin_api:${env.BUILD_TAG}")
      }
      stage('system tests') {
          sh "./run_systemtests.sh -e system -- --runslow"
      }
      stage('proxy system tests') {
          sh "./run_systemtests.sh -e proxy -- --runslow"
      }
    }
  } catch (e) {
    currentBuild.result = "FAILED"
  } finally {
    setPhabricatorBuildStatus env.PHID
  }
}
