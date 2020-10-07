from tkinter import *
from bs4 import BeautifulSoup
import re
import random
import requests


class Cell:
    def __init__(self, cell_label, color=None):
        self.cell_label = cell_label
        self.color = color


class Courses:
    def __init__(self, days, hours):
        self.days = days
        self.hours = hours


class Data:
    def __init__(self, courses, word_dct, cells):
        # a dictionary for the courses objects, key is the course code
        self.courses = courses
        # a dictionary of all words and corresponding course objects
        self.word_dct = word_dct
        # a dictionary of the calender cells. Key is the weekday, the value is another dictionary, where the key is the
        # starting time of the cell, the value is the Cell object
        self.cells = cells


class GUI(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent

        header = Label(self, text='Sehir Course Planner', bg='#8a9eff', font=('Calibri', '20'))
        header.pack(fill=X)
        frame1 = Frame(self, bg='MintCream')
        frame1.pack()
        Label(frame1, text='Course Offerings Url:', bg='MintCream').grid(row=0, column=0, columnspan=2)
        self.entry_url = Entry(frame1, width=50)
        self.entry_url.grid(row=0, column=2, columnspan=3)
        self.entry_url.insert(0, 'https://www.sehir.edu.tr/tr/duyurular/2019_2020_akademik_yili_bahar_donemi_ders_programi')
        fetch_button = Button(frame1, text='Fetch Courses')
        fetch_button.grid(row=0, column=5)
        fetch_button.bind("<Button-1>", self.fetch)

        Label(frame1, text='Filter:', bg='MintCream').grid(row=1, column=0)
        sv = StringVar()
        sv.trace("w", lambda name, index, mode, sv=sv: self.filter(sv))
        self.filter_entry = Entry(frame1, width=30, textvariable=sv)
        self.filter_entry.grid(row=1, column=1, columnspan=2, padx=(0, 8))
        Label(frame1, text='Selected Courses', bg='MintCream').grid(row=1, column=4, columnspan=3)
        self.not_added_label = Label(frame1)
        self.not_added_label.grid(column=4, row=1, columnspan=3, sticky=E, padx=(0, 10))

        self.previous_selected_courses = None  # this is later used for the fetch function
        self.filtered_listbox = Listbox(frame1, width=50, height=5)
        self.filtered_listbox.grid(row=2, column=0, columnspan=3, rowspan=2, sticky=E, padx=10)
        self.filtered_listbox.bind('<<ListboxSelect>>', self.listbox_selection)
        self.filtered_listbox.propagate(False)
        scrollbar1 = Scrollbar(self.filtered_listbox)
        scrollbar1.pack(side=RIGHT, fill=Y)
        self.filtered_listbox.config(yscrollcommand=scrollbar1.set)
        scrollbar1.config(command=self.filtered_listbox.yview)

        self.add_button = Button(frame1, text='Add', font=('Calibri', '12', 'bold'))
        self.add_button.grid(row=2, column=3)
        self.add_button.bind('<Button-1>', self.add_course)
        self.remove_button = Button(frame1, text='Remove', font=('Calibri', '12', 'bold'))
        self.remove_button.grid(row=3, column=3)
        self.remove_button.bind('<Button-1>', self.remove_course)

        self.selected_listbox = Listbox(frame1, width=50, height=5, selectmode=MULTIPLE)
        self.selected_listbox.grid(row=2, column=4, columnspan=3, rowspan=2, sticky=W, padx=10)
        self.selected_listbox.propagate(False)
        scrollbar2 = Scrollbar(self.selected_listbox)
        scrollbar2.pack(side=RIGHT, fill=Y)
        self.selected_listbox.config(yscrollcommand=scrollbar2.set)
        scrollbar2.config(command=self.selected_listbox.yview)

        self.cell_colors = ['dodger blue', 'pale turquoise', 'dark turquoise', 'plum', 'mediumvioletred', 'cyan',
                  'cadet blue', 'medium aquamarine', 'tomato', 'LemonChiffon4', 'cornsilk2', 'cornsilk4',
                  'honeydew2', 'dark orchid', 'hot pink', 'blue violet', 'purple']

        frame2 = Frame(self, bg='MintCream')
        frame2.pack(pady=5, padx=10)
        black_label = Label(frame2, bg='black', width=11, height=1)
        black_label.grid(column=0, row=0)
        # the labels for the days get created
        days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i in range(7):
            Label(frame2, bg='#00CCFF', width=11, height=1, text=days_list[i]).grid(column=i+1, row=0)

        self.data = Data({}, {}, {})
        # the labels for the time get created
        time_counter = 1
        first_hour = 9
        first_hour_counter = 0
        second_hour = 9
        second_hour_counter = 1
        for i in range(26):
            if time_counter == 1:
                if first_hour_counter == 1:
                    first_hour += 1
                    first_hour_counter = 0
                minutes = '00'
                other_minutes = '30'
                time_counter -= 1
                first_hour_counter += 1
            else:
                if second_hour_counter == 1:
                    second_hour += 1
                    second_hour_counter = 0
                minutes = '30'
                other_minutes = '00'
                time_counter += 1
                second_hour_counter += 1

            Label(frame2, bg='#00CCFF', width=11, height=1,
                  text='%d:%s-%d:%s' % (first_hour, minutes, second_hour, other_minutes)).grid(column=0, row=i+1)

            # the labels for the cells get created
            for t in range(7):
                cell_label = Label(frame2, bg='green', width=10, height=1)
                cell_label.grid(column=t+1, row=i+1, padx=1, pady=1)
                # dictionary for the cells get created, that looks like the following:
                # {Monday:{(9,00):cell object, (9,30):cell object, (10, 00):cell object, ...}  , Tuesday:... }
                self.data.cells.setdefault(days_list[t], {})
                self.data.cells[days_list[t]][(first_hour, minutes, second_hour, other_minutes)] \
                    = Cell(cell_label)

    # to filter out the '\n' that are in some of the strings
    def clean(self, string):
        pattern = re.compile('\n')
        return re.sub(pattern, '', string)

    def fetch(self, event):
        r = requests.get(self.entry_url.get())
        page = r.content
        soup = BeautifulSoup(page, 'html.parser')

        # getting the courses from the webpage and saving them in classes
        lst = [item.text for item in soup.find_all('p', class_='MsoNormal')]
        counter = 0
        for i in range(int(len(lst)/6)-1):
            counter += 6
            course_code = lst[counter]
            uncleaned_days = lst[2+counter]
            uncleaned_hours = lst[3+counter]
            days = self.clean(uncleaned_days)
            hours = self.clean(uncleaned_hours)
            # only considering those who have both days and hours
            if len(days) <= 1 or len(hours) <= 1:
                continue
            words = [word.lower() for word in (' '.join([course_code, days, hours]).split())]
            self.data.courses[course_code] = Courses(days, hours)
            # a dictionary with all the words, the values are a list with the course codes that correspond to that word
            for word in words:
                self.data.word_dct.setdefault(word, [])
                self.data.word_dct[word].append(course_code)
        # insert everything into the listbox
        for course_code, course_obj in self.data.courses.items():
            self.filtered_listbox.insert(END, course_code + ' ' + course_obj.days + ' ' + course_obj.hours)

    def filter(self, sv):
        # filtering the courses depending on the keywords of the entry field
        search_words = sv.get()
        splitted_words = search_words.split()
        # a dictionary gets created, key is the course and value how many times a keyword correspond to the course
        search_dct = {}
        for word in splitted_words:
            for dct_words, courses in self.data.word_dct.items():
                # when part of the word is in the dicitonary word, it gets added
                if word in dct_words:
                    for course in courses:
                        search_dct.setdefault(course, 0)
                        search_dct[course] += 1
        # a list gets created for all the courses that correspond to all of the keywords
        results = []
        for course, count in search_dct.items():
            if count == len(splitted_words):
                results.append(course)
        # old results get deleted
        self.filtered_listbox.delete(0, END)
        # if there are results, they get inserted into the listbox
        if results:
            for result in results:
                self.filtered_listbox.insert(END, result + ' ' + self.data.courses[result].days + ' ' +
                                             self.data.courses[result].hours)
        # if the entry field is empty, all the courses will be shown
        if not search_words:
            for course_code, course_obj in self.data.courses.items():
                self.filtered_listbox.insert(END, course_code + ' ' + course_obj.days + ' ' + course_obj.hours)

    # a function that compares two times and returns if it is lesser or greater or some time
    def compare_time(self, hour1, minute1, hour2, minute2):
        time1 = int(hour1)*60 + int(minute1)
        time2 = int(hour2)*60 + int(minute2)

        p = 0  # means both times are equal
        if time1 > time2:
            p += 1  # means first time is greater than the second
        elif time1 < time2:
            p -= 1  # means second time is greater than the first
        return p

    # a function to return a list of cell objects that are currently selected through the courses in the listbox.
    # it takes the course code that is currently selected, and returns a list of all the cell objects in the dictionary
    # that are between the start and ending time of the course
    def selected_cells(self, selected_course_codes):
        selected_cells_list = []
        for course in selected_course_codes:
            times = self.data.courses[course].hours.split()
            days_of_course = self.data.courses[course].days.split()

            # for the case that only one time was given to more than one day:
            if len(times) < len(days_of_course):
                if len(times) == 1:
                    for time in times:
                        # how many times to add the same time
                        number = len(days_of_course) - len(times)
                        for i in range(number):
                            times.append(time)

            zipped_courses = zip(days_of_course, times)

            for day, hours_of_course in zipped_courses:
                hours_course = hours_of_course.split('-')
                start_time = hours_course[0].split(':')
                end_time = hours_course[1].split(':')
                hour_start_time = start_time[0]
                minute_start_time = start_time[1]
                hour_end_time = end_time[0]
                minute_end_time = end_time[1]

                for firsthour, firstminute, endhour, endminute in self.data.cells[day].keys():  # every cell of this day
                    if self.compare_time(hour_start_time, minute_start_time, firsthour, firstminute) == 0 or \
                       self.compare_time(hour_start_time, minute_start_time, firsthour, firstminute) == -1 and \
                       self.compare_time(hour_end_time, minute_end_time, endhour, endminute) == 1 or \
                       self.compare_time(hour_start_time, minute_start_time, firsthour, firstminute) == -1 and \
                       self.compare_time(hour_end_time, minute_end_time, endhour, endminute) == 0:

                        # add it to the list of cells
                        selected_cells_list.append(self.data.cells[day][firsthour, firstminute, endhour, endminute])
        return selected_cells_list

    # a function to filter out the course code out of the string in the listboxes
    def filter_course_codes(self, course_list):
        course_codes = []
        for course in course_list:
            pattern = re.compile(".+?(?=\s\w\w\w\w\w\w+)")
            result = pattern.search(course)
            course_codes.append(result.group())
        return course_codes

    # the event handler for clicking on a selection in the left listbox
    def listbox_selection(self, event):
        # the 'could not be added' label is made invisible
        self.not_added_label.configure(text='', bg='MintCream')
        selected_courses = [self.filtered_listbox.get(i) for i in self.filtered_listbox.curselection()]
        # the course codes of the selection gets filtered out
        selected_course_codes = []
        if selected_courses:
            selected_course_codes = self.filter_course_codes(selected_courses)

        # make the deselection of the course
        if self.previous_selected_courses:
            selected_cells = self.selected_cells(self.previous_selected_courses)
            # change the label back to green
            for cell in selected_cells:
                if cell.cell_label.cget('bg') == 'yellow':
                    cell.cell_label.configure(bg='green')
                # if the cell was red because of overlapping, it will return to the color it had before
                elif cell.cell_label.cget('bg') == 'red':
                    cell.cell_label.configure(bg=cell.color)

        # the current list of selected courses gets saved as the previous one
        self.previous_selected_courses = selected_course_codes

        # the selected courses get colored yellow, or red if they are not green
        selected_cells = self.selected_cells(selected_course_codes)
        for cell in selected_cells:
            if cell.cell_label.cget('bg') == 'green':
                cell.cell_label.configure(bg='yellow')
            # if the cell is already colored in another color, it should color it red, showing that courses overlap
            elif cell.cell_label.cget('bg') != 'green':
                cell.cell_label.configure(bg='red')

    # the event handler to add a course
    def add_course(self, event):
        selected_cells = self.selected_cells(self.previous_selected_courses)
        if selected_cells:
            # checking if one of the cells is overlapping
            overlap = None
            for cell in selected_cells:
                if cell.cell_label.cget('bg') == 'red':
                    overlap = True
                    # adding the label, by configuring it
                    self.not_added_label.configure(text='Could not be added', bg='red')
                    break
            # if it doesn't overlap the cells get colored and the other listbox filled
            if not overlap:
                color = random.choice(self.cell_colors)
                for cell in selected_cells:
                    cell.color = color
                    cell.cell_label.configure(bg=color)
                    for course in self.previous_selected_courses:
                        cell.cell_label.configure(text=course)
                self.cell_colors.remove(color)
                self.selected_listbox.insert(END, self.filtered_listbox.get(self.filtered_listbox.curselection()))

    # the event handler to delete a course
    def remove_course(self, event):
        selected_courses = [self.selected_listbox.get(i) for i in self.selected_listbox.curselection()]
        if selected_courses:
            # the courses get deleted from the listbox
            for course in selected_courses:
                idx = self.selected_listbox.get(0, END).index(course)
                self.selected_listbox.delete(idx)
            # the cells get identified, and the color set back to green
            selected_course_codes = self.filter_course_codes(selected_courses)
            cells_of_course = self.selected_cells(selected_course_codes)
            deleted_color_list = []
            for cell in cells_of_course:
                deleted_color = cell.cell_label.cget('bg')
                if deleted_color not in deleted_color_list:
                    deleted_color_list.append(deleted_color)
                # if the course is deleted from the selected list, the cell will also go back to being green
                cell.color = None
                cell.cell_label.configure(bg='green')
                cell.cell_label.configure(text='')
            # the color of the deleted cell gets added back to the list of colors
            self.cell_colors.extend(deleted_color_list)


def main():
    root = Tk()
    root.title('Sehir Course Planner')
    app = GUI(root)
    app.configure(bg='MintCream')
    app.pack(fill=BOTH, expand=TRUE)
    root.mainloop()

if __name__ == '__main__':
    main()
