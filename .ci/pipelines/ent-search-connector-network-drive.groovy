//
// Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
// or more contributor license agreements. Licensed under the Elastic License 2.0;
// you may not use this file except in compliance with the Elastic License 2.0.
//

// Loading the shared lib
@Library(['apm', 'estc', 'entsearch']) _

eshPipeline(
    timeout: 45,
    project_name: 'Enterprise Search Network Drive Connector',
    repository: 'enterprise-search-network-drives-connector',
    stages: [
        [
            name: 'Make Lint',
            type: 'script',
            label: 'Makefile',
            script: {
                sh 'docker run -v `pwd`:/ci -w=/ci --rm --name jenkins-linter -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:3 make lint'
            },
            match_on_all_branches: true,
        ]
    ]
)