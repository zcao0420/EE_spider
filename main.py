# This is a web spider designed to get information about Canada Express Entry draw
# It can get the history data including lowest CRS score drawn, Number of candidates drawn
# of each draw. The id and date of each draw can also be recorded.
# Another function of this program is to get the most recently updated candidate pool information.
# Given a person's CRS score, it can determine the rank in pool of that person.

import requests
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
import pymysql as sql
import time
# bs4 need lxml to work, make sure to install lxml

# Define the class for each draw
class draw_info:

    def __init__(self):
        self.score_url = 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/' \
                         'express-entry/submit-profile/rounds-invitations/' \
                         'results-previous.html/'  # The draw score url
        self.pool_url = 'https://www.canada.ca/en/immigration-refugees-citizenship/' \
                        'services/immigrate-canada/express-entry/submit-profile/' \
                        'rounds-invitations.html'  # The candidate pool url
        self.scores = []
        self.rounds = []
        self.dates = []
        self.N_candidates = []
        self.programs = []
        self.pool = []
        self.total_candidates = 0

    def reverse_list(self):
        self.scores.reverse()
        self.rounds.reverse()
        self.dates.reverse()
        self.N_candidates.reverse()
        self.programs.reverse()

    def modify_date(self):
        date_dict = {'January': 'Jan',
                     'February': 'Feb',
                     'March': 'Mar',
                     'April': 'Apr',
                     'May': 'May',
                     'June': 'Jun',
                     'July': 'Jul',
                     'August': 'Aug',
                     'September': 'Sep',
                     'October': 'Oct',
                     'November': 'Nov',
                     'December': 'Dec'}
        new_dates = []
        for date in self.dates:
            changed = date.replace("\xa0", " ")
            for key, value in date_dict.items():
                changed = changed.replace(key, value)
            new_dates.append(changed)
        self.dates = new_dates

    def parse_score_url(self):
        # Get all info under class <p> in html
        req = requests.get(url=self.score_url)
        content = bs(req.text, features = "lxml")
        texts = content.find_all('p')
        # Parse information into each list
        for text in texts:
            line = text.get_text()
            if 'CRS' in line:
                self.scores.append(int(line[-3:]))
            if 'Number of invitations' in line:
                substring = line[30:].replace(',','').replace('Footnote *','')
                self.N_candidates.append(int(substring))
            if 'rogram' in line or 'Canadian Experience Class' in line:
                if '.' not in line:
                    if 'No program' in line:
                        normal = 1
                        self.programs.append(normal)
                    elif 'Programs' in line:
                        normalA = 0
                        normalB = 0
                        self.programs.append(normalA)
                        self.programs.append(normalB)
                    else:
                        normal = 0
                        self.programs.append(normal)
        # Get all info under class <td> in html
        # Those are old draw scores and number of candidates (before Nov 1st 2017)
        texts = content.find_all('td')
        for text in texts:
            line = text.get_text()
            if 'points' in line:
                score = int(line[:3])
                self.scores.append(score)
            else:
                if ',' in line:
                    line = line.replace(',', '')
                candidates = int(line)
                self.N_candidates.append(candidates)

        # Get all info under class <h3> in html
        texts = content.find_all('h3')
        # Parse information into each list
        for text in texts:
            line = text.get_text()
            if "#" in line:
                round = line.split(' – ')[0][1:]
                date = line.split(' – ')[1]
                if round == '91':
                    roundA = '91A'
                    roundB = '91B'
                    self.rounds.append(roundA)
                    self.rounds.append(roundB)
                    self.dates.append(date)
                    self.dates.append(date)
                else:
                    self.rounds.append(round)
                    self.dates.append(date)

        # Reverse lists
        self.reverse_list()

    def parse_pool_url(self):
        # Get information from pool url
        # Including most recent draw and candidate pool distribution

        # The most recent draw
        req = requests.get(url=self.pool_url)
        content = bs(req.text, features = "lxml")
        texts = content.find_all('p')
        for text in texts:
            line = text.get_text()
            if 'CRS score of lowest-ranked' in line:
                self.scores.append(int(line[-3:]))
            if 'Number of invitations' in line:
                substring = line[30:].replace(',', '').replace('Footnote *','')
                self.N_candidates.append(int(substring))
            if 'rogram' in line or 'Canadian Experience Class' in line:
                if '.' not in line:
                    if 'No program' in line:
                        normal = 1
                        self.programs.append(normal)
                    elif 'Programs' in line:
                        normalA = 0
                        normalB = 0
                        self.programs.append(normalA)
                        self.programs.append(normalB)
                    else:
                        normal = 0
                        self.programs.append(normal)
            if 'Date and time' in line:
                # date starts from the 24th character after split
                substring = line.split(' at ')[0][24:]
                self.dates.append(substring)

        # Most recent round number is previous one plus 1
        self.rounds.append(str(int(self.rounds[-1])+1))

        # The candidates pool
        gen_dist = []
        # General distribution
        texts = content.find_all('td')
        for text in texts:
            line = text.get_text()
            substring = line.replace(',','')
            gen_dist.append(int(substring))
        del gen_dist[2]
        del gen_dist[7]
        # Combine lists
        self.pool = gen_dist[:-1]
        self.total_candidates = gen_dist[-1]
        print(self.pool)
        print(self.total_candidates)
        # Reverse pool
        self.pool.reverse()


    def retrieve_info(self):
        self.parse_score_url()
        self.parse_pool_url()

        # Modify dates
        self.modify_date()

    def plot_general_draw(self, period = 'quarter'):
        length_dict = {'quarter' : 6,
                       'month': 2,
                       'half year': 12,
                       'annual': 24,
                       'all': len(self.rounds)}
        length = length_dict[period]
        x = []
        y = []
        for i, normal in enumerate(self.programs):
            if normal:
                x.append(self.dates[i])
                y.append(self.scores[i])
        plt.plot(x[-length:], y[-length:])
        plt.scatter(x[-length:], y[-length:])

        # Make the plot look better
        plt.tick_params(axis = 'both', direction = 'in', width = 1.5)
        plt.xticks(rotation = -90, fontsize = 12)
        plt.yticks(fontsize = 13)
        plt.xlabel('Draw date', fontsize = 15)
        plt.ylabel('CRS score of lowest ranked candidate', fontsize = 15)
        plt.tight_layout()
        # Show plot
        plt.show()

    def plot_candidates_dist(self):
        x = ['0','300','350','360','370','380','390','400','410','420',
             '430','440','450','600']
        bars = plt.bar(x,self.pool, width = 1.0, align = 'edge', linewidth = 1, edgecolor = 'k')
        # Add data annotations on bar plot
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x()+bar.get_width()/2.0, height, self.pool[i],
                     ha = 'center', va = 'bottom')

        # Make the plot look better
        plt.tick_params(axis='x', width=0)
        plt.tick_params(axis='y', direction = 'in', width = 1.5)
        plt.xticks(fontsize = 13)
        plt.yticks(fontsize = 13)
        plt.xlabel('CRS scores', fontsize = 15)
        # Show plot
        plt.ylabel('Number of candidates', fontsize = 15)
        plt.show()

    def myRank(self, score):
        intervals = [0,301,351,361,371,381,391,401,411,421,431,441,451,601,1201]
        position  = -1
        for i in range(len(intervals)-1):
            if score in range(intervals[i], intervals[i+1]):
                position = i
                break
        # If position is -1 then the score input is invalid
        # return immediately
        if position == -1:
            print('Invalid CRS score')
            return

        # If the input score is valid, then calculate the bottom and top rank possible
        rank_bot = -1
        rank_top = -1
        rank_bot = sum(self.pool[position:])
        if position == 13:
            rank_top = 1
        else:
            rank_top = sum(self.pool[position+1:])
        print('With your score: %d, you rank between %dth to %dth '
              'in candidate pool' %(score, rank_top, rank_bot))
        return

    def check_length(self):
        print('program', len(self.programs))
        print('N candidates', len(self.N_candidates))
        print('scores', len(self.scores))
        print('rounds', len(self.rounds))
        print('dates', len(self.dates))

    def combine_data(self):
        # Make sure the lengths of lists are the same
        assert len(self.scores) == len(self.rounds) \
               == len(self.N_candidates) == len(self.dates)
        combined = []
        for i, score in enumerate(self.scores):
            combined.append([self.rounds[i], self.dates[i],
                             score, self.N_candidates[i]])
        dated_pool = self.pool
        dated_pool.insert(0, self.dates[-1])
        return combined, dated_pool

class MYSQL:

    def __init__(self):
        # Connect
        self.conn = sql.connect(
            host="database-1.cmzzciuuvgtr.us-east-2.rds.amazonaws.com",
            port=int(3306),
            user='Johnny',
            passwd='James970420',
            db="Canada_EE",
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()
        return

    def table_check(self, table_name):
        command = 'SHOW TABLES'
        self.cursor.execute(command)
        output_tuple = self.cursor.fetchall()
        output_list = [x[0] for x in output_tuple]
        check = table_name in output_list
        return check

    def update_draw(self, combined):
        insert_element = """
            INSERT INTO Draws (DrawID, Date, Score, Population)
            VALUES (%s, %s, %s, %s)
        """
        create_draws = """
            CREATE TABLE Draws (
                DrawID varchar(10) NOT NULL,
                Date varchar(20) NOT NULL,
                Score INT NOT NULL,
                Population INT NOT NULL
            )
        """
        select = """
            SELECT * FROM Draws
        """
        name = 'Draws'
        latest = combined[-1]
        if self.table_check(name):
            """
            If the table exist,
            first check if the latest draw on record is
            the same as in combined data.
            If no, then only insert the latest draw to table.
            If yes, do nothing.
            """
            self.cursor.execute(select)
            table = self.cursor.fetchall()
            if table[-1][0] != latest[0]:
                self.cursor.execute(insert_element,
                                    (latest[0], latest[1],
                                     latest[2], latest[3]))
                self.conn.commit()
            else:
                return
        else:
            """
            If the specific table does not exist,
            then create the table before inserting
            each draw info into the table
            """
            self.cursor.execute(create_draws)
            for draw in combined:
                self.cursor.execute(insert_element,
                                    (draw[0], draw[1], draw[2], draw[3]))
                self.conn.commit()
        return

    def update_pool(self, pool):
        create_pool = """
            CREATE TABLE Pool (
            Date varchar(20) NOT NULL,
            Lv1 INT NOT NULL,
            Lv2 INT NOT NULL,
            Lv3 INT NOT NULL,
            Lv4 INT NOT NULL,
            Lv5 INT NOT NULL,
            Lv6 INT NOT NULL,
            Lv7 INT NOT NULL,
            Lv8 INT NOT NULL,
            Lv9 INT NOT NULL,
            Lv10 INT NOT NULL,
            Lv11 INT NOT NULL,
            Lv12 INT NOT NULL,
            Lv13 INT NOT NULL,
            Lv14 INT NOT NULL
            )
        """

        select = """
            SELECT * FROM Pool
        """
        delete_first = """
            DELETE FROM Pool LIMIT 1
        """
        insert_pool = """
            INSERT INTO Pool 
            (Date, Lv1, Lv2, Lv3, Lv4, Lv5, Lv6, Lv7,
                Lv8, Lv9, Lv10, Lv11, Lv12, Lv13, Lv14)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s)
        """
        name = 'Pool'
        if self.table_check(name):
            self.cursor.execute(select)
            table = self.cursor.fetchall()
            print(table)
            if table[0][0] != pool[0]:
                self.cursor.execute(delete_first)
                self.conn.commit()
                self.cursor.execute(insert_pool,
                                    (pool[0], pool[1], pool[2], pool[3],
                                     pool[4], pool[5], pool[6], pool[7],
                                     pool[8], pool[9], pool[10], pool[11],
                                     pool[12], pool[13], pool[14]))
                self.conn.commit()
            else:
                return
        else:
            self.cursor.execute(create_pool)
            self.cursor.execute(insert_pool,
                                (pool[0], pool[1], pool[2], pool[3],
                                 pool[4], pool[5], pool[6], pool[7],
                                 pool[8], pool[9], pool[10], pool[11],
                                 pool[12], pool[13], pool[14]))
            self.conn.commit()
        return

    def update_time(self):
        delete_first = """
                    DELETE FROM Update_time LIMIT 1
                """
        insert_time = """
                    INSERT INTO Update_time
                    (update_time)
                    VALUES 
                    (%s)
                """
        current_time = str(time.ctime())

        self.cursor.execute(delete_first)
        self.conn.commit()
        self.cursor.execute(insert_time,(current_time))
        self.conn.commit()
        print('Update time: %s' %current_time)
        return

    def disconnect(self):
        self.conn.close()
        return


if __name__ == '__main__':
    # Create a draw_info class
    info = draw_info()
    # Retrieve all data from Internet
    info.retrieve_info()
    # Get the data to be updated
    to_update, dated_pool = info.combine_data()

    ##########################
    # Create connection to AWS RDS
    database = MYSQL()
    # Update draw info and pool info
    database.update_draw(to_update)
    database.update_pool(dated_pool)
    database.update_time()
    # Disconnect from the database
    database.disconnect()
    print("Update finished at " + time.ctime())
