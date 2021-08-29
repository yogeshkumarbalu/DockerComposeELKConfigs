node {
  stage('SCM') {
    git branch: 'main', url: 'https://github.com/yogeshkumarbalu/DockerComposeELKConfigs.git'
  }
  stage('SonarQube Analysis') {
    def scannerHome = tool 'sonarscanner';
    withSonarQubeEnv('sonarqube') {
      sh "${scannerHome}/bin/sonar-scanner"
    }
  }
}
