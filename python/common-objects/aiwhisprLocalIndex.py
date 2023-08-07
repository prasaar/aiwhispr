import sqlite3
import logging

class aiwhisprLocalIndex:
   def __init__(self,index_log_directory,content_site_name):
      self.index_log_directory = index_log_directory
      self.content_site_name = content_site_name
      dbfilename=index_log_directory+ '/' + content_site_name + '.db'
      
      self.logger = logging.getLogger(__name__)
      
      self.connection = sqlite3.connect(dbfilename)
      try:
         self.connection.execute("CREATE TABLE IF NOT EXISTS ContentMetaMap(content_site_name TEXT,src_path TEXT,src_path_for_results TEXT,content_path TEXT,content_type TEXT,content_creation_date REAL,content_last_modified_date REAL,content_uniq_id_src TEXT, content_tags_from_src TEXT, content_size INTEGER,content_file_suffix TEXT, content_index_flag TEXT, content_processed_status TEXT, rsync_status TEXT);" )
      except:
         self.logger.error('Error when running SQLite statement to create ContentMetaMap table')
         
      try:
         self.connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS content_path_unique_idx on ContentMetaMap(content_path);')
         self.connection.execute('CREATE INDEX IF NOT EXISTS content_processed_status_idx on ContentMetaMap(content_processed_status);') 
         self.connection.execute('CREATE INDEX IF NOT EXISTS rsync_status_idx on ContentMetaMap(rsync_status);')
      except:
         self.logger.error('Error when running SQLite statement to create indices on ContentMetaMap table')
         

   def insert(self,content_site_name, src_path, src_path_for_results, content_path, content_type, content_creation_date, content_last_modified_date, content_uniq_id_src, content_tags_from_src, content_size, content_file_suffix, content_index_flag, content_processed_status, rsync_status):
       
      insert_string = "INSERT INTO ContentMetaMap(content_site_name, src_path, src_path_for_results, content_path, content_type, content_creation_date, content_last_modified_date, content_uniq_id_src, content_tags_from_src, content_size, content_file_suffix, content_index_flag, content_processed_status, rsync_status) VALUES("
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
      insert_string = insert_string + "'" + content_processed_status + "',"
      insert_string = insert_string + "'" + rsync_status + "')"
      try:
         self.connection.execute(insert_string)
      except:
         self.logger.error("Error when inserting into ContentMetaMap using SQLite : %s", insert_string )



   def deleteAll(self):
      listOfTables = self.connection.execute( """SELECT name FROM sqlite_master WHERE type='table' AND name='ContentMetaMap'; """).fetchall()
      if len(listOfTables) == 0:
         self.logger.info('In deleteAll .... ContentMetaMap table not found. Nothing to delete!')
      else:
         self.logger.info('Deleting from table ContentMetaMap!')
         self.connection.execute("DELETE FROM ContentMetaMap;")   


   def getContentProcessedStatus(self,content_processed_status):
      query_string = "SELECT content_site_name,src_path,src_path_for_results,content_path,content_type,content_creation_date,content_last_modified_date,content_uniq_id_src,content_tags_from_src,content_size,content_file_suffix, content_index_flag,content_processed_status  FROM ContentMetaMap WHERE content_processed_status = '" + content_processed_status + "'"
      res = self.connection.execute(query_string)
      return res.fetchall()
