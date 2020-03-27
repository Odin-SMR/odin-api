node() {
  def odinapiImage
  def proxyImage
  stage('git') {
    checkout scm
  }
  stage('javascript unit tests') {
      sh "npm install && npm update && npm test"
  }
  stage('build odinapi') {
    odinapiImage = docker.build("docker2.molflow.com/odin_redo/odin_api")
  }
  stage('build proxy') {
    proxyImage = docker.build("docker2.molflow.com/odin_redo/proxy", "services/proxy")
  }
  stage('tests') {
      sh "tox -- --runslow"
  }
  if (env.GITREF == 'master') {
    stage('push') {
      odinapiImage.push(env.BUILD_TAG)
      odinapiImage.push('latest')
      proxyImage.push(env.BUILD_TAG)
      proxyImage.push('latest')
    }
  }
}
