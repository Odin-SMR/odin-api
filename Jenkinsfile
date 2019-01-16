@Library('molflow') _

node() {
  def odinapiImage
  try {
      stage('git') {
        checkout scm
      }
      stage('python unit tests') {
          sh "./run_unittests.sh -- --runslow"
      }
      stage('javascript unit tests') {
          sh "npm install && npm update && npm test"
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
      if (env.GITREF == 'master') {
        stage('push') {
          odinapiImage.push()
          odinapiImage.push('latest')
        }
      }
  } catch (e) {
    currentBuild.result = "FAILED"
    throw e
  } finally {
    setPhabricatorBuildStatus env.PHID
  }
}
