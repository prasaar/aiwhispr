import sqlite3

class aiwhisprLocalIndex:
    def __init__(self,index_log_directory,content_site_name):
       self.index_log_directory = index_log_directory
       self.content_site_name = content_site_name
       dbfilename=index_log_directory+ '/' + content_site_name + '.db'
       self.connection = sqlite3.connect(dbfilename)
         

    def insert(self,content_site_name, src_path, src_path_for_results, content_path, content_type, content_creation_date, content_last_modified_date, content_uniq_id_src, content_tags_from_src, content_size, content_file_suffix, content_index_flag, content_processed_status):
       self.connection.execute("CREATE TABLE IF NOT EXISTS ContentIndex( content_site_name TEXT,src_path TEXT,src_path_for_results TEXT,content_path TEXT,content_type TEXT,content_creation_date REAL,content_last_modified_date REAL,content_uniq_id_src TEXT, content_tags_from_src TEXT, content_size INTEGER,content_file_suffix TEXT, content_index_flag TEXT, content_processed_status TEXT)")

       insert_string = "INSERT INTO ContentIndex(content_site_name, src_path, src_path_for_results, content_path, content_type, content_creation_date, content_last_modified_date, content_uniq_id_src, content_tags_from_src, content_size, content_file_suffix, content_index_flag, content_processed_status) VALUES("
       insert_string = insert_string + "'" + content_site_name + "'," 
       insert_string = insert_string + "'" + src_path + "'," 
       insert_string = insert_string + "'" + src_path_for_results + "'," 
       insert_string = insert_string + "'" + content_path + "'," 
       insert_string = insert_string + "'" + content_type + "'," 
       insert_string = insert_string + str(content_creation_date) + "," + str(content_last_modified_date) + ","
       insert_string = insert_string + "'" + content_uniq_id_src + "',"
       insert_string = insert_string + "'" + content_tags_from_src + "',"
       insert_string = insert_string + str(content_size) + ","
       insert_string = insert_string + "'" + content_file_suffix + "',"
       insert_string = insert_string + "'" + content_index_flag + "',"
       insert_string = insert_string + "'" + content_processed_status + "')"

       self.connection.execute(insert_string)
      
    def purge(self):
       self.connection.execute("DELETE FROM ContentIndex")   


    def getIndexStatus(self,index_status):
       query_string = "SELECT content_site_name,src_path,src_path_for_results,content_path,content_type,content_creation_date,content_last_modified_date,content_uniq_id_src,content_tags_from_src,content_size,content_file_suffix, content_index_flag,index_status  FROM ContentIndex WHERE index_status = '" + index_status + "'"
       res = self.connection.execute(query_string)
       return res.fetchall()
