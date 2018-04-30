import sys, os, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from src.functions import * # all functions required to make the analysis

# then modules for GUI
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pylab as plt
plt.style.use('ggplot')
from PyQt5 import QtGui, QtWidgets, QtCore

Blue, Orange, Green, Red, Purple, Brown, Pink, Grey,\
    Kaki, Cyan = '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',\
    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'

FONTSIZE= 5
matplotlib.rcParams.update({'axes.labelsize': FONTSIZE,
                            'axes.titlesize': FONTSIZE,
                            'figure.titlesize': FONTSIZE,
                            'font.size': FONTSIZE,
                            'xtick.labelsize': FONTSIZE,
                            'ytick.labelsize': FONTSIZE})

def create_plot_window(parent, hspace=0.1, left=0.08, right=0.99, bottom=0.2, figsize=(8,3)):

    width, height = parent.screensize[0]/1.1, parent.screensize[1]/1.5
    
    fig_large_view, AX_large_view = plt.subplots(3, 1, figsize=(figsize[0], figsize[1]/1.5))
    plt.subplots_adjust(hspace=hspace, left=left, right=right, bottom=1.5*bottom)
    AX_large_view[0].set_xticklabels([])
    AX_large_view[1].set_xticklabels([])
    # AX_large_view[2].set_xlabel('time (s)')
        
    fig_zoom, AX_zoom  = plt.subplots(3, 1, figsize=(figsize[0], figsize[1]))
    plt.subplots_adjust(hspace=hspace, left=left, right=right, bottom=bottom)
    AX_zoom[0].set_xticklabels([])
    AX_zoom[1].set_xticklabels([])
    AX_zoom[2].set_xlabel('time (s)')
            
    for ax1, ax2, label in zip(AX_large_view, AX_zoom,
                               ['$V_{ext}$ ($\mu$V)', 'pLFP ($\mu$V)', 'NSI ($\mu$V)']):
        ax1.set_ylabel(label+'              ', rotation=0)
        ax2.set_ylabel(label)
        ax1.set_yticks([])
    
    # Window size choosen appropriately
    window = QtWidgets.QDialog()
    window.setGeometry(10, 150, width, height)

    # this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    
    canvas_large_view = FigureCanvas(fig_large_view)
    canvas_zoom = FigureCanvas(fig_zoom)

    toolbar_zoom = NavigationToolbar(canvas_zoom, window)
    toolbar_zoom.hide()
    
    layout = QtWidgets.QGridLayout(window)
    layout.addWidget(canvas_large_view)
    layout.addWidget(canvas_zoom)
    layout.addWidget(toolbar_zoom)
        
    window.setLayout(layout)
            
    return window, AX_large_view, AX_zoom, canvas_large_view, canvas_zoom

class Window(QtWidgets.QMainWindow):
    
    def __init__(self, app, parent=None, DATA_LIST=None, KEYS=None):
        
        super(Window, self).__init__(parent)
        
        # buttons and functions
        LABELS = ["q) Quit", "o) Open File", "r) Run analysis", "s) Save as .bin",
                  "Save as txt", "z) Zoom1", "Zoom2"]
        FUNCTIONS = [self.close_app, self.file_open, self.analyze, self.close_app,\
                     self.close_app, self.close_app, self.close_app]
        button_length = 130
        self.setWindowTitle('Computing the Network State Index')
        self.setGeometry(50, 50, button_length*(1+len(LABELS)), 60)
        
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('&File')
        
        screen = app.primaryScreen()
        rect = screen.availableGeometry()
        self.screensize = rect.width(), rect.height()

        for func, label, shift in zip(FUNCTIONS, LABELS,\
                                      button_length*np.arange(len(LABELS))):
            btn = QtWidgets.QPushButton(label, self)
            btn.clicked.connect(func)
            btn.setMinimumWidth(button_length)
            btn.move(shift, 0)
            action = QtWidgets.QAction(label, self)
            action.setShortcut(label.split(')')[0])
            action.triggered.connect(func)
            self.fileMenu.addAction(action)
        
        # self.statusBar().showMessage('Provide a datafile for the analysis... (with "Open File" or the keyboard shortcut "o")')
        
        self.window,\
            self.AX_large_view, self.AX_zoom,\
            self.canvas_large_view, self.canvas_zoom = create_plot_window(self)
        self.window.show()    
        self.show()

        # data initializaton
        self.data = {'Extra':[], 'pLFP':[], 'NSI_validated':[], 't_validated':[], 'NSI':[], 'dt':[]}

        # program defaults
        try:
            self.params = dict(np.load('data/last_params.npz'))
        except (FileNotFoundError, ValueError, IndexError, TypeError):
            self.params = {'xlim':[0,50]}
        
        self.filename, self.folder = 'data/sample_data.npz', 'data/'
        self.load_data(self.filename)
        self.large_scale_plot()
        self.zoom_plot()
        
    def load_data(self, filename):
        self.statusBar().showMessage('loading data [...]')
        loaded_data = dict(np.load(filename))
        for key in loaded_data:
            self.data[key] = loaded_data[key]
        self.dt = self.data['dt']
        self.nsamples = len(self.data['Extra'])
        self.statusBar().showMessage('Data loaded, now "Run Analysis"')
        
    def large_scale_plot(self, Nplot=2000):
        
        # large scale version
        lfp_to_plot = self.data['Extra'][::int(self.nsamples/Nplot)]
        self.AX_large_view[0].plot(np.arange(len(lfp_to_plot))*self.data['dt']*int(self.nsamples/Nplot),
                                   lfp_to_plot, lw=0.5, color=Grey)
        for ax in self.AX_large_view:
            ax.set_xlim([0, self.dt*self.nsamples])
        self.ylim0 = self.AX_large_view[0].get_ylim()
        self.ylim1 = self.AX_large_view[1].get_ylim()
        self.ylim2 = self.AX_large_view[2].get_ylim()

    def large_scale_plot_NSI(self, Nplot=2000):
        
        # large scale version
        Nsamples = len(self.data['pLFP'])
        plfp_to_plot = self.data['pLFP'][::int(Nsamples/Nplot)]
        self.AX_large_view[1].plot(np.arange(len(plfp_to_plot))*self.data['new_dt']*int(Nsamples/Nplot),
                                   plfp_to_plot, lw=0.5, color=Brown)
        cond1 = self.data['NSI_validated'] & (self.data['NSI']>0)
        self.AX_large_view[2].plot(self.data['new_t'][cond1], self.data['NSI'][cond1], '.', ms=0.2, color=Kaki)
        cond2 = self.data['NSI_validated'] & (self.data['NSI']<=0)
        self.AX_large_view[2].plot(self.data['new_t'][cond2], self.data['NSI'][cond2], '.', ms=0.2, color=Purple)
        self.ylim1 = np.min(plfp_to_plot), np.max(plfp_to_plot)
        self.ylim2 = np.min(self.data['NSI'][self.data['NSI_validated']]), np.max(self.data['NSI'][self.data['NSI_validated']])
        self.canvas_large_view.draw()
        
    def zoom_plot(self, Nplot=2000):

        # cleaning up the plot before:
        for ax in self.AX_zoom:
            while len(ax.lines)>0:
                del ax.lines[-1] # removing the previous plots
        
        i1, i2 = int(self.params['xlim'][0]/self.dt), int(self.params['xlim'][1]/self.dt)
        lfp_to_plot = self.data['Extra'][i1:i2][::int((i2-i1)/Nplot)]
        self.AX_zoom[0].plot(np.arange(len(lfp_to_plot))*self.data['dt']*int((i2-i1)/Nplot),
                             lfp_to_plot, lw=0.5, color=Grey)
        self.AX_zoom[0].set_xlim([i1*self.dt, i2*self.dt])

        if len(self.data['pLFP'])>0:
            
            i1, i2 = int(self.params['xlim'][0]/self.data['new_dt']), int(self.params['xlim'][1]/self.data['new_dt'])
            # plotting pLFP variations
            plfp_to_plot = self.data['pLFP'][i1:i2][::int((i2-i1)/Nplot)]
            self.AX_zoom[1].plot(np.arange(len(plfp_to_plot))*self.data['new_dt']*int((i2-i1)/Nplot),
                                 plfp_to_plot, lw=1, color=Brown)
            self.AX_zoom[1].set_xlim([i1*self.data['new_dt'], i2*self.data['new_dt']])
            
            # plotting NSI variations
            nsi_to_plot = self.data['NSI'][i1:i2][::int((i2-i1)/Nplot)]
            self.AX_zoom[2].plot(np.arange(len(plfp_to_plot))*self.data['new_dt']*int((i2-i1)/Nplot),
                                 nsi_to_plot, lw=0.5, color='k')
            self.AX_zoom[2].set_xlim([i1*self.data['new_dt'], i2*self.data['new_dt']])

            # plotting validated NSI
            cond = self.data['NSI_validated'] &\
                   (self.data['new_t']>self.params['xlim'][0]) &\
                   (self.data['new_t']<=self.params['xlim'][1])
            self.AX_zoom[2].plot(self.data['new_t'][cond & (self.data['NSI']>0)],
                                 self.data['NSI'][cond & (self.data['NSI']>0)], 'o',
                                 ms=1, color=Kaki)
            self.AX_zoom[2].plot(self.data['new_t'][cond & (self.data['NSI']<=0)],
                                 self.data['NSI'][cond & (self.data['NSI']<=0)], 'o',
                                 ms=1, color=Purple)
            
        self.canvas_zoom.draw()
            
        # highlighting zoom area in the large plot
        i1, i2 = int(self.params['xlim'][0]/self.dt), int(self.params['xlim'][1]/self.dt)
        for ax, ylim in zip(self.AX_large_view, [self.ylim0, self.ylim1, self.ylim2]):
            while len(ax.collections)>0:
                del ax.collections[-1] # removing the previous highlight !
            ax.fill_between([i1*self.dt, i2*self.dt], np.ones(2)*ylim[0], np.ones(2)*ylim[1], color='r', alpha=.2, lw=0)
            ax.set_ylim(ylim)
        self.canvas_large_view.draw()
        
    def analyze(self):
        self.statusBar().showMessage("Analyzing data [...]")
        preprocess_LFP(self.data)
        compute_Network_State_Index(self.data)
        # now updating plots
        self.large_scale_plot_NSI()
        self.zoom_plot()
        self.statusBar().showMessage("Data Analyzed !")
    
    def file_open(self):
        name=QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',\
                                                   self.folder)
        try:
            self.filename = name[0]
            self.folder = os.path.dirname(self.filename)
        except FileNotFoundError:
            self.statusBar().showMessage('/!\ No datafile found... ')
            # pass

    def close_app(self):
        if self.params is not None:
            np.savez('data/last_params.npz', **self.params)
        sys.exit()

    def folder_open(self):
        name=QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', self.folder)
        if name!='':
            self.folder = name
        else:
            self.folder = os.path.sep+'tmp'
        self.analysis_flag = False
        try:
            rename_files_for_easy_sorting(dir=self.folder)
            # we first rename the files (add 0, so that '23_01_13' instead of '23_1_13')
            self.set_analysis_folder()
            self.i_plot = 0
            self.FILE_LIST = get_list_of_files(self.folder)
            self.filename = self.FILE_LIST[self.i_plot]
            self.update_params_and_windows()
        except (IndexError, FileNotFoundError, NoneType, OSError):
            self.statusBar().showMessage('/!\ No datafile found... ')
            
    def save_as_data(self):
        i=1
        while os.path.isfile(os.path.join(self.analysis_folder, 'data'+str(i)+'.npz')):
            i+=1
        save_as_npz(self, os.path.join(self.analysis_folder, 'data'+str(i)+'.npz'))
        self.statusBar().showMessage('Saving as : '+os.path.join(self.analysis_folder, 'data'+str(i)+'.npz'))


if __name__ == '__main__':
    import time
    app = QtWidgets.QApplication(sys.argv)
    main = Window(app)
    # main.show()
    sys.exit(app.exec_())