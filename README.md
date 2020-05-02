### QUICK HIRE

This project is part of the data science group for Labs project Quick Hire. Quick hire is a one stop job application portal for specifically for Lambda School students. 

You can find the live project at [QuickHire.dev](https://quickhire.dev)

## Quickhire DS-Data Description

This repository holds code for the Models and Web Scraper of Quick Hire. It also includes documentation for the code until the migration to FastAPI with its automatically generated documentation is complete. It will also include tests from Starlette (comes with FastAPI) once migration is complete. 

### Methods Used

* Web Scraping
* Machine Learning
* Predictive Modeling
* Deep Learning (to be implemented)
* Code Coverage/Automated Testing (to be implemented)

### Tech Stack

* Python
* Pandas, Jupyter
* FastAPI
* Starlette
* Selenium 
* PostgresSQL 
* AWS Elastic Beanstalk 
* AWS Lambda Functions
* AWS RDS

## QuickHire DS-Data More Detailed Description

The scraper, application.py uses Selenium to scrape Monster.com. Pre-processing is done with some basic data cleaning and also some feature engineering with Spacey. The production model is KNearestNeighbors which is not yet deployed to live searches.  WARNING: DO NOT RENAME IT FROM application.py, AWS is looking for a file named application.py and it will break on production/master if you re-name and then push.

Model stuff is in datafunctions.

The database (PostgreSQL) is hosted on AWS RDS (database-1). A summary of the structure can be found at docs/db_structure/db_structure.md, and schema details at docs/db_structure/awsrds.schema.

The web application is hosted on AWS elastic beanstalk. The documentation can be found here: https://github.com/Lambda-School-Labs/Job-Funnel-ds-API/blob/master/docs/api/reference.md until migration to FastAPI is complete.

Test Suite not implemented yet but to be updated here. 

# QuickHire DS-Data Documentation

Documentation for the models can be found in models.md

Documentation for the API can be found https://api.quickhire.dev/ for: 
* project architecture 
* database structure and schema 
* API/ / reference (until migration to FastAPI is complete)
* project status (pending, may move here) 
* lambda functions deployed to AWS.

See [Backend Documentation](https://github.com/Lambda-School-Labs/Job-Funnel-be) for details on the backend of our project.
See [Frontend Documentation](https://github.com/Lambda-School-Labs/Job-Funnel-fe) for details on the frontend of our project.

## Needs of this Project

TBD

## Getting Started

NOTE: Master branch of this code is already running live on AWS. If you are the next Lambda School Team to build on, you will inherit the AWS instances and also be given lectures on how to use the various AWS services. 

Nonetheless, if you want to work on this locally:

1. Clone this repo. 

2. Clone the other repo which has the web scraper and models: https://github.com/Lambda-School-Labs/Job-Funnel-ds-Data

3. Create your own database and login credentials setup since the .gitignore has our live database credentials. Install any libraries from requirements of both repos that weren't added. 

4. Run the scraper in the other repo to begin populating the data base.

## Featured Notebooks/Tutorials/Additional Resources 

 To be updated

## Contributing

Full Name: Github : Slack Handle 

Please note we have a [code of conduct](./code_of_conduct.md.md). Please follow it in all your interactions with the project.

### Issue/Bug Request

 **If you are having an issue with the existing project code, please submit a bug report under the following guidelines:**
 - Check first to see if your issue has already been reported.
 - Check to see if the issue has recently been fixed by attempting to reproduce the issue using the latest master branch in the repository.
 - Create a live example of the problem.
 - Submit a detailed bug report including your environment & browser, steps to reproduce the issue, actual and expected outcomes,  where you believe the issue is originating from, and any potential solutions you have considered.

### Feature Requests

We would love to hear from you about new features which would improve this app and further the aims of our project. Please provide as much detail and information as possible to show us why you think your new feature should be implemented.

### Pull Requests

If you have developed a patch, bug fix, or new feature that would improve this app, please submit a pull request. It is best to communicate your ideas with the developers first before investing a great deal of time into a pull request to ensure that it will mesh smoothly with the project.

Remember that this project is licensed under the MIT license, and by submitting a pull request, you agree that your work will be, too.

#### Pull Request Guidelines

- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the README.md with details of changes to the interface, including new plist variables, exposed ports, useful file locations and container parameters.
- Ensure that your code conforms to our existing code conventions and test coverage.
- Include the relevant issue number, if applicable.
- You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

### Attribution

These contribution guidelines have been adapted from [this good-Contributing.md-template](https://gist.github.com/PurpleBooth/b24679402957c63ec426).

## Project Overview

https://github.com/Lambda-School-Labs/Job-Funnel-ds-API/tree/master/docs

[Trello Board](https://trello.com/b/dorhqi4o/job-funnel)

[Product Canvas](https://www.notion.so/Job-Funnel-20ba287fac1c403c92a8ebb8766821a0)

[UX Design files](https://www.figma.com/file/zljtkyosMyzAa1UMpcAIEd/Quick-Hire-Judy?node-id=263%3A2)

## Template Link for this README

https://github.com/sfbrigade/data-science-wg/blob/master/dswg_project_resources/Project-README-template.md

[Backend Documentation](https://github.com/Lambda-School-Labs/Job-Funnel-be)

[Data Science Repo](https://github.com/Lambda-School-Labs/Job-Funnel-ds-API)
