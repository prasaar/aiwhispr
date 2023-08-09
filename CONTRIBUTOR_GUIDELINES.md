## Design guidelines to keep in mind when contributing source code 
- The software should be easy to install.Installations instructions shoule be easy to read, simple to execute.
- The configuration names should recognizable for the audience (developer/system administrator/user) who will be configuring the value.    
- A semantic search engine should have fast response times for search queries. Take more time for data preparation, indexing if it helps improve the search response time.
- A semantic search engine should be able to ingest content from both on OS, cloud (e.g. Azure Blob, AWS S3 ) with simple configuration, no code changes.
- A semantic search engine should be able to ingest multiple file types. If a file type is not handled then code changes should be minimum to add additional support for a file type.
- A semantic search engine should clean the data before it submits it to the LLM for encoding. 
- A semantic search engine should be able to run in multiple levels of logging (DEBUG,CRITICAL,ERROR, INFO) so that developers, system administrators can monitor the health, setup alerts.
- Every feature will be built on community feedback.Feedback from users will define the desired outcome of the feature.

