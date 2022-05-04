#!/bin/bash -e

# Update the sonar-project.properties file
sed -e "s|{{SONAR_QUBE_BRANCH}}|$TRAVIS_BRANCH|" \
-e "s|{{SONAR_QUBE_PROJ_KEY}}|$SONAR_QUBE_PROJ_KEY|" \
$PATH_SONAR_PROPERTIES > $PATH_SONAR_PROPERTIES.tmp && mv $PATH_SONAR_PROPERTIES.tmp $PATH_SONAR_PROPERTIES

# Run the sonar-scanner
/tmp/sonar-scanner-$SONAR_SCANNER_VERSION-linux/bin/sonar-scanner -Dsonar.host.url=$SONAR_QUBE_URL -Dsonar.login=$SONAR_QUBE_TOKEN

# Get analysis status
python $PATH_SCRIPTS_DIR/get_sonarqube_project_status.py "$SONAR_QUBE_URL" "$SONAR_QUBE_TOKEN" "$SONAR_QUBE_PROJ_KEY" "$TRAVIS_BRANCH"
