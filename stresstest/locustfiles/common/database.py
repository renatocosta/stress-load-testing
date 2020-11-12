import os
from sqlalchemy import create_engine


class database():
    __mypool = False

    def query(self, sql, params=False):
        sql_connection = 'mysql+pymysql://%s:%s@%s:%s/%s' % (os.environ['MYSQL_USER'], os.environ['MYSQL_PASSWORD'], os.environ['MYSQL_HOST'], os.environ['MYSQL_PORT'], os.environ['MYSQL_DATABASE'])
        
        self.__mypool = create_engine(sql_connection, pool_size=500, pool_recycle=120)
        conn = self.__mypool.connect()
        if params:
            results = conn.execute(sql, params)
        else:
            results = conn.execute(sql)
        conn.close()

        return results

    def fetchone(self, sql):
        results = self.query(sql=sql)
        return results.fetchone()
