pipeline {
	agent any
	stages {
		stage("Copy docker compose file to ELK Docker server") {
			steps {
				sshPublisher(publishers: [sshPublisherDesc
					(configName: 'ElkDockerHost', transfers: [sshTransfer(cleanRemote: false, excludes: '', execCommand: '', execTimeout: 0, 
						flatten: false, makeEmptyDirs: false, noDefaultExcludes: false, patternSeparator: '[, ]+', remoteDirectory: '.', 
						remoteDirectorySDF: false, removePrefix: '', sourceFiles: '*.yml, *.py')], 
						usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)])
			}
		}

		stage("Copy the python test scripts and docker compose file to Ansible server and execute the playbook") {
			steps {
				sshPublisher(publishers: [sshPublisherDesc
					(configName: 'AB-Ansible', transfers: [sshTransfer(cleanRemote: false, excludes: '', 
						execCommand: 'ansible-playbook test-play.yml', execTimeout: 0, flatten: false, 
						makeEmptyDirs: false, noDefaultExcludes: false, patternSeparator: '[, ]+', 
						remoteDirectory: '.', remoteDirectorySDF: false, removePrefix: '', sourceFiles: '*.yml, *.py')], 
					usePromotionTimestamp: false, useWorkspaceInPromotion: false, verbose: false)])
			}
		}
		
	}
}
