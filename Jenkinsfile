pipeline {
	agent any
	stages {
		
		
		  stage('SonarQube Analysis') {
			    def scannerHome = tool 'sonarqube';
			    withSonarQubeEnv('sonarqube') {
			      sh "${scannerHome}/bin/sonar-scanner"
		}
		
		
		
	}
}
