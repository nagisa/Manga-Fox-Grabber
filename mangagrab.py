#!/usr/bin/python
from threading import Thread, activeCount
import gtk
import time
from gobject import threads_init, idle_add
import re
import urllib2
from urllib import urlencode
from sgmllib import SGMLParser
import os
from reportlab.platypus import SimpleDocTemplate, Image
import Image as PImage
import shutil
threads_init()


class MainWindow(gtk.Window):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.checked = False
        self.connect("destroy", self.do_exit)
        self.set_size_request(400, 150)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_title('MangaFox Grabber')
        try:
            self.set_icon_from_file('logo.png')
        except:
            pass

        halign = {}
        vbox = gtk.VBox(False, 2)
        hbox = {}

        self.progress = gtk.ProgressBar()
        self.progress.set_text("Press Check, when ready.")
        self.button = gtk.Button('Check')
        self.button.connect('clicked', self.on_continue)
        self.help = gtk.Button('How to use this application?')
        self.help.connect('clicked', self.on_help)
        self.entry = gtk.Entry()
        self.entrylabel = gtk.Label('Manga')

        self.threads = gtk.combo_box_new_text()
        for sel in ['5 threads(slowest, most stable)',
                    '10 threads(recommended)',
                    '20 threads',
                    '50 threads (fastest, least stable)']:
            self.threads.append_text(sel)
        self.threads.set_active(1)

        self.selection = gtk.combo_box_new_text()
        for sel in ['A5 page size',
                    'A4 page size',
                    'A3 page size']:
            self.selection.append_text(sel)
        self.selection.set_active(0)

        widgs = [[self.progress],
                [self.threads],
                [self.selection],
                [self.entrylabel, self.entry],
                [self.button, self.help], ]

        for key, widgets in enumerate(widgs):
            halign[key] = gtk.Alignment(1, 0, 1, 0)
            hbox[key] = gtk.HBox(False, 2)
            for widget in widgets:
                hbox[key].add(widget)
            halign[key].add(hbox[key])
            vbox.pack_start(halign[key], False, False, 1)

        self.add(vbox)
        self.show_all()

    def on_continue(self, widget):
        ##Block buttons
        self.button.set_sensitive(False)
        ##Do Step 2 if done.
        if self.checked:
            self.progress.set_fraction(0)
            step = StepTwoContainer(self.links)
            step.start()
            return True
        ##Set URL fetching thingy.
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.98 Safari/534.13'}
        self.urllib = urlencode({'name': 'Grabber', 'location': 'Hell', 'language': 'Python', 'port': 80, 'timeout': 10})
        self.regex = re.compile('http://[a-zA-Z0-9.-_]*/store/manga/[0-9]*/[0-9-.]*/compressed/[a-zA-Z0-9._-]*.jpg')
        ##Set application cache
        self.links = []
        self.images = {}
        self.temps = []
        self.seriesLen = 0
        ##Set some healthy variables
        self.currentDir = os.getcwd()
        self.force = False
        self.completed = 0
        ##Get user input
        self.series = self.entry.get_text()
        self.maxThreads = self.get_threads()
        self.psize = self.get_psize()
        step = StepOne()
        step.start()

    def on_help(self, widget):
        from webbrowser import open as webopen
        webopen('https://github.com/simukis/Manga-Fox-Grabber/blob/master/HOWTO')

    def get_threads(self):
        active = self.threads.get_active()
        if active == 0:
            return 5
        elif active == 1:
            return 10
        elif active == 2:
            return 20
        elif active == 3:
            return 30
        else:
            return 10

    def get_psize(self):
        from reportlab.lib.pagesizes import A3, A4, A5
        active = self.selection.get_active()
        if active == 0:
            return A5
        elif active == 1:
            return A4
        elif active == 2:
            return A3
        else:
            return A5

    def get_author(self):
        try:
            url = 'http://www.mangafox.com/manga/'+self.series+'/?no_warning=1'
            request = urllib2.Request(url, self.urllib, self.headers)
            content = urllib2.urlopen(request).read()
            a=re.compile('<th>Author\(s\)</th>(.*?)<td><a href="/search/author/(.*?)/" style="color:#666">(.*?)</a></td>', re.MULTILINE| re.DOTALL)
            return a.search(content).group(3)
        except:
            return 'Unknown'

    def do_exit(self, widget):
        os._exit(0)


class URLLister(SGMLParser):

    def reset(self):
        SGMLParser.reset(self)
        self.urls = []

    def start_a(self, attrs):
        href = [v for k, v in attrs if k=='href']
        if href:
            self.urls.extend(href)


class StepOne(Thread):

    def __init__(self):
        super(StepOne, self).__init__()

    def update_status(self, value=None, text=None):
        if value != None:
            interface.progress.set_fraction(value)
        if text != None:
            interface.progress.set_text(text)
        return False

    def run(self):
        try:
            idle_add(self.update_status, 0, 'Fetching author')
            interface.author = interface.get_author()
            idle_add(self.update_status, 0.05, 'Fetching page')
            url = 'http://www.mangafox.com/manga/'+interface.series+'/?no_warning=1'
            request = urllib2.Request(url, interface.urllib, interface.headers)
            content = urllib2.urlopen(request).read()
            idle_add(self.update_status, 0.2, 'Processing page')
            parser = URLLister()
            parser.feed(content)
            linkslen = len(parser.urls)
            currentFraction = 0.2
            for link in parser.urls:
                if interface.series in link and not "rss" in link and not link in interface.links and '1.html' in link:
                    interface.links.append(link)
                currentFraction+=0.799/linkslen
                idle_add(self.update_status, currentFraction)
            interface.links.reverse()
            idle_add(self.update_status, 1, 'Done. Press Download to proceed.')
            interface.button.set_label('Download')
            interface.checked = True
            interface.seriesLen = len(interface.links)
        except:
            idle_add(self.update_status, 0, 'Cannot correctly get info. Check manga field.')
        finally:
            interface.button.set_sensitive(True)


class StepTwoContainer(Thread):

    def __init__(self, links):
        super(StepTwoContainer, self).__init__()
        self.links = links

    def update_status(self, value=None, text=None):
        if value != None:
            interface.progress.set_fraction(value)
        if text != None:
            interface.progress.set_text(text)
        return False

    def run(self):
        thrds = []
        for link in self.links:
            while activeCount() >= interface.maxThreads:
                time.sleep(0.1)
            step = StepTwo(link)
            thrds.append(step)
            step.start()
        for thrd in thrds:
            thrd.join()
        for dire in interface.temps:
            shutil.rmtree(dire)
        idle_add(self.update_status, 1, 'Done, do anything else if you want.')
        interface.checked=False
        interface.button.set_label('Check')
        interface.button.set_sensitive(True)


class StepTwo(Thread):

    def __init__(self, link):
        super(StepTwo, self).__init__()
        self.link = link
        self.images = []

    def update_status(self, value=None, text=None):
        if value != None:
            interface.progress.set_fraction(value)
        if text != None:
            interface.progress.set_text(text)
        return False

    def run(self):
        linkbundle = self.link.split('/')[-3:][:2]
        if linkbundle[0] == interface.series:
            linkbundle[0] = '/'
        else:
            linkbundle[0] = '/'+linkbundle[0]+'/'
        ##Check if not downloaded already.
        try:
            chapters = os.listdir(interface.series)
        except:
            chapters = []
        if linkbundle[1]+'.pdf' in chapters and not interface.force:
            interface.completed = interface.completed+1.0/interface.seriesLen
            idle_add(self.update_status, interface.completed, 'Chapter '+linkbundle[1].strip('c')+' was found downloaded.')
            return True
            ##Completed that chapter!
        idle_add(self.update_status, None, 'Start reading chapter '+linkbundle[1].strip('c'))
        for page in range(1, 1000):
            url = 'http://www.mangafox.com/manga/'+interface.series+linkbundle[0]+linkbundle[1]+'/'+str(page)+'.html'
            request = urllib2.Request(url, interface.urllib, interface.headers)
            try:
                content = urllib2.urlopen(request).read()
            except:
                continue
            try:
                image=interface.regex.search(content).group(0)
                if not image in self.images:
                    self.images.append(image)
                else:
                    break ##Chapter END
            except:
                print 'Could not get image for chapter '+linkbundle[1]+' page '+str(page)
                break ##Could not get image!
        interface.completed = interface.completed+(0.25/interface.seriesLen)
        idle_add(self.update_status, interface.completed, 'Downloading chapter '+linkbundle[1].strip('c'))
        ###
        ##Downloading images.
        ###
        chapterLen = len(self.images)
        if chapterLen < 2:
            interface.completed = interface.completed+(0.75/interface.seriesLen)
            idle_add(self.update_status, interface.completed, 'Done chapter '+linkbundle[1].strip('c'))
            return True
        try:
            os.mkdir(interface.series)
        except:
            pass
        try:
            os.mkdir(os.path.join(interface.series, linkbundle[1]))
        except:
            pass
        for image in self.images:
            imagename=image.split('/')[-1]
            img = open(os.path.join(interface.series, linkbundle[1], imagename), 'w')
            img.write(urllib2.urlopen(image).read())
            img.close()
            interface.completed = interface.completed+(0.5/interface.seriesLen/chapterLen)
            idle_add(self.update_status, interface.completed, None)
        ###
        ##Making PDF
        ###
        c=SimpleDocTemplate(os.path.join(interface.series, linkbundle[1]+'.pdf'),
                            pagesize=interface.psize,
                            rightMargin=0,
                            leftMargin=0,
                            topMargin=0,
                            bottomMargin=0)
        Story=[]
        maxh = interface.psize[1]-20
        maxw = interface.psize[0]-30
        title=' '.join(interface.series.split('_'))
        c.title=title+' '+linkbundle[1]
        c.author=interface.author
        directory=os.path.join(interface.series, linkbundle[1])
        images=sorted(os.listdir(directory))
        for image in images:
            img = PImage.open(os.path.join(directory, image))
            width, height = img.size
            img = img.crop(( 0, 0, width, height-40))
            img.save(os.path.join(directory, image))
            img = PImage.open(os.path.join(directory, image))
            width, height = img.size
            if width/maxw>height/maxh:
                height=height/(width/maxw)
                width=maxw
                if width>height:
                    img = img.rotate(90)
                    img.save(os.path.join(directory, image))
                    width, height = img.size
                    if width/maxw>height/maxh:
                        height=height/(width/maxw)
                        width=maxw
                    else:
                        width=width/(height/maxh)
                        height=maxh
            else:
                width=width/(height/maxh)
                height=maxh
            im = Image(os.path.join(directory, image), width, height)
            Story.append(im)
        c.build(Story)
        interface.completed = interface.completed+(0.2499/interface.seriesLen)
        idle_add(self.update_status, interface.completed, 'Done chapter '+linkbundle[1].strip('c'))
        interface.temps.append(os.path.join(interface.series, linkbundle[1]))


interface = MainWindow()
gtk.main()
