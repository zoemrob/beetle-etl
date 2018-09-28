# How to Contribute
To start off, thank you for your interest in being apart of the Beetle project! We are eager to incorporate your awesome contributions.


# Contributor License Agreement
For more information, see our LICENSE.md file.


# Getting Setup
1. Clone the Beetle Repository

2. Install required dependancies (see more info in README.md)


# Code Reviews
All submissions require review from an Interject Repository Administrator (Robby Boney or Adam Rodriguez ) before being merged to the master branch. To accomplish this, submissions should be presented with GitLab's merge request feature. 

For more information on GitLab Merge Requests see (https://docs.gitlab.com/ee/gitlab-basics/add-merge-request.html) 


# Commit Messages
We believe commit messages are very important for code readability and communication which helps a project thrive and grow. As such, Commit messages should follow the Semantic Commit Messages format:

```
label(namespace): title

description

footer
```

1. _label_ should be one of the following
    - `fix` - beetle bug fixes
    - `feat` - beetle features
    - `opt` - code optimization
    - `docs` - changes to documentation (i.e. `docs(README.md)` )
    - `test` - changes to beetle
    - `style` - beetle code style: spaces/alignment/line wrapping
    - `chore` - build-related work
2. _namespace_ is put in parenthesis after label and refers to the topic or file
3. _title_ is a brief description summary of changes
3. _description_ is an *optional*, new-line separated from _title_
5. _footer_ is an *optional*, new-line separated from _description_ and contains references to gitlab issues or relevent information.


```
feat(OrientDBController): added filter to OrientDB pull  

added ability to perform simple filtering with OrientDB pulls  

Feature #154
```


# Adding New Dependencies
For all dependencies:
- Do not add new dependencies if the functionality can be accomplished easily without the dependency
- If the dependency must be added, it should be a trustable project
Due to the critical nature of dependencies for a package submissions involving new dependencies will be more heavily scrutinized before they are merged.

> It should be noted that new controllers allowing for wider support for databases is encouraged


# Writing Tests
- Every Beetle service feature should be accompanied by a test
- Tests should not depend on external services
- Tests should work on all three platforms: Mac, Linux and Windows

Beetle tests are located in `/Beetle-ETL/Beetle_Src/Beetle/tests` and are written using pytest. 

> For more information on [**pytest**](https://docs.pytest.org/en/latest/)

> For more information on **Beetle Testing**, see `README#Testing`