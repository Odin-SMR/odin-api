node() {
  def odinapiImage
  def proxyImage
  stage('git') {
    checkout scm
  }
  stage('build bundle for ui') {
      sh "npm install && npm run build"
  }
  stage('javascript unit tests') {
      sh "npm test"
  }
  stage('build odinapi') {
    odinapiImage = docker.build("odinsmr/odin_api")
  }
  stage('build proxy') {
    proxyImage = docker.build("odinsmr/proxy", "services/proxy")
  }
  stage('tests') {
      sh "tox -r -- --runslow"
  }
  stage('cleanup') {
      sh "rm -r .tox"
  }
  if (env.BRANCH_NAME == 'master') {
    stage('push') {
      withDockerRegistry([ credentialsId: "dockerhub-molflowbot", url: "" ]) {
        odinapiImage.push(env.BUILD_TAG)
        odinapiImage.push('latest')
        proxyImage.push(env.BUILD_TAG)
        proxyImage.push('latest')
      }
    }
  }
}
