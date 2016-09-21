import sqlite3, sys, os, webbrowser
from bs4 import BeautifulSoup as soup

class sql_table(object):
    """A class that contains many hand method for operating on a sqlite database."""
    def __init__(self,tb_name,db_object):
        self.name = tb_name
        self.db = db_object
        pass
    def entry(self,data):
        if type(data) != list:
            raise Exception("Got %s when expecting a list." % (type(data).__name__))
        data = str(data).replace("[","").replace("]","")
        # str and then replace instead of ", ".join() so I don't have to worry about quotes.
        sb = "INSERT INTO %s VALUES(%s)" % (self.name,data)
        self.db.c.execute(sb)
        self.db.conn.commit()
        pass
    def get_raw(self):
        sb = "SELECT * FROM %s" % (self.name)
        self.db.c.execute(sb)
        return self.db.c.fetchall()
    def get_column_names(self):
        sb = "SELECT * FROM %s" % (self.name)
        self.db.c.execute(sb)
        return list(map(lambda x: x[0], self.db.c.description))
    def get_values(self,filter_by="value", **kwargs):
        """
        This is a very limiting function, that simply filters the output depending if the row has a certain column equal to a certain value.
        Example:
            filter_by_value(values=[["username","jhon"]],filter_by="value")
            where the output row's username columns must be equal to "jhon".
        NOTE:
            If this function isn't exact enough, just use regular sqlite syntax, using self.db.c.execute(<YOUR SQLITE CODE>)
        """
        if filter_by == "value":
            try:
                kwargs["values"]
                if type(kwargs["values"]) != list:
                    raise Exception("Expected list for value keyword argument, but got%s" % (type(kwargs.item()[0][1])))
            except KeyError:
                raise Exception("filter_by was set to \"value\", but no value keyword argument was supplied.")
            l = kwargs["values"]
            sb = []
            for i in l:
                sb.append("%s='%s'" % (i[0],i[1]))
            sb = " AND ".join(sb)
            fcmd = "SELECT * FROM %s WHERE %s" % (self.name,sb)
            self.db.c.execute(fcmd)
            return self.db.c.fetchall()
    def to_html(self):
        """Generates HTML table for table data"""
        names = self.get_column_names()
        l = self.get_raw()
        tree = soup("<table><tbody></tbody></table>", "html.parser")
        body = tree.find("tbody")
        # create th tags for all the column names
        tr = tree.new_tag("tr")
        for name in names:
            th = tree.new_tag("th")
            th.append(name)
            tr.append(th)
        body.append(tr)
        # now go through rows of data
        for row in l:
            r = tree.new_tag("tr")
            for item in row:
                ttag = tree.new_tag("td")
                if type(item) == str:
                    ttag.append("\"%s\"" % (item))
                else:
                    ttag.append(str(item))
                r.append(ttag)
            body.append(r)
        return tree
    def display_html(self, use_stylesheet=True):
        path_to_html_cache = "cache/generated_table.html"
        base = soup("<html><head></head><body></body></html>", "html.parser")
        base.find("body").append(self.to_html())
        title = base.new_tag("title")
        title.append(self.db.filename + " | " + self.name)
        base.find("head").append(title)
        if use_stylesheet:
            r = open("src/html/stylesheets/sqlite_db_table.css",'r')
            x = base.new_tag("style")
            x.append(r.read())
            r.close()
            base.find("head").append(x)
        if os.path.exists(path_to_html_cache) == False:
            open(path_to_html_cache,'a')
        w = open(path_to_html_cache, 'w')
        w.write(str(base))
        w.close()
        webbrowser.open_new_tab("file://" + os.getcwd().replace("\\","/") + "/" + path_to_html_cache)

class database(object):
    datatype_conversion = {
        int : "REAL",
        float : "REAL",
        str : "TEXT"
        }
    def __init__(self,filename):
        self.conn = sqlite3.connect(filename)
        self.c = self.conn.cursor()
        self.filename = filename
        tables = self.get_tables()
        if tables != None:
            for name in tables:
                try:
                    self.__setattr__(name,sql_table(name,self))
                except:
                    print("Encountered Error where indexing all the database's tables. Perhaps your database has an issue with its names?")
                    print("(Error encountered):")
                    print(str(sys.exc_info()[1]))
        pass
    def create_table(self,name,sample,if_not_exists=True):
        """
        Creates an sqlite table.
        PROTOCAL FOR SAMPLE ARGUMENT:
            [
                <name of column>, <sample value (for data type) >
            ]
        """
        strb = []
        for i in sample:
            try:
                strb.append(i[0] + " " + self.datatype_conversion[type(i[1])])
            except KeyError:
                raise Exception("Unknown data type for %s" % (i[1]))
                sys.exit(1)
        strb = ", ".join(strb)
        ifnot = ""
        if if_not_exists:
            ifnot = "IF NOT EXISTS "
        self.c.execute("CREATE TABLE %s%s(%s)" % (ifnot,name,strb))
        self.__setattr__(name,sql_table(name,self))
        pass
    def close_all(self):
        """closes the cursors and connections for the database"""
        self.c.close()
        self.conn.close()
        pass
    def get_tables(self):
        """Returns all of the database's tables"""
        self.c.execute("select name from sqlite_master where type = 'table'")
        return self.c.fetchall()
