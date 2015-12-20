# -*- encoding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib.font_manager import FontManager
# use seaborn plotting style defaults
import seaborn as sns
import subprocess
import re


def supported_chinese_font():
    fm = FontManager()
    mat_fonts = set(f.name for f in fm.ttflist)

    output = subprocess.check_output('fc-list :lang=zh -f "%{family}\n"', shell=True)
    # print '*' * 10, '系统可用的中文字体', '*' * 10
    # print output
    zh_fonts = set(f.split(',', 1)[0] for f in output.split('\n'))
    available = mat_fonts & zh_fonts

    print '*' * 10, '可用的中文字体', '*' * 10
    for f in available:
        print f
    return available


class DidaEventLog(object):
    """ Event log for dida365.com """
    def __init__(self, datafile=None, routine_duration=12):
        """ create a event log for dida365.com

        datafile: 数据文件全路径名，数据文件可以从 dida365.com 的设置里导出，是一个 csv 格式的文件
        routine_duration: 每天花在其他事情上的平均时长，比如常规的吃喝拉撒睡等，单位小时

        时间小偷：routine_duration 作为一般性数据输入，便于统计出“时间小偷”。
        在做数据统计时，除了有记录的工作时间花销外，会扣除每天固定的时间花销，剩余的没被记录的时间就是时间小偷。
        我们要尽量想办法抢回被时间小偷偷走的时间。时间小偷可能是你发呆的时间，无效率的时间，做无用功的时间。
         """
        sns.set()
        mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']    # 指定默认字体
        mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

        self.datafile = datafile
        self.routine_duration = routine_duration
        self.cached = False
        self.data_raw = None
        self.data_days = None
        self.start_day = None
        self.end_day = None

    def _process_data(self):
        """ read data from inpt file and parse tags and durations """

        def _parse_tag(value):
            m = re.match(r'^(\[(.*?)\])?.*$', value)
            if m and m.group(2):
                return m.group(2)
            else:
                return '其他'

        def _parse_duration(value):
            m = re.match(r'^.+?\[(.*?)([hm]?)\]$', value)
            if m:
                dur = 0
                try:
                    dur = float(m.group(1))
                except Exception, e:
                    print('parse duration error: \n%s' % e)
                if m.group(2) != 'm':
                    dur = dur * 60
                return int(dur)
            else:
                return 0

        # real data is from the third line
        raw = pd.read_csv(self.datafile, header=3, index_col='Due Date', parse_dates=True)
        # only process the completed/archived items
        data = raw[raw['Status'] != 0].loc[:, ['List Name', 'Title']]
        # parse tags and duration
        titles = data['Title']
        data['Tag'] = titles.map(_parse_tag)
        data['Duration'] = titles.map(_parse_duration)
        # calcute total duration
        self.start_day = str(pd.Timestamp(data.index.values.min()).date())
        self.end_day = str(pd.Timestamp(data.index.values.max()).date())
        self.data_raw = data
        # cache days data
        days_data = data.groupby(level=0).sum()
        days_data['Thief'] = ((24 - self.routine_duration) * 60) - days_data['Duration']
        days_data['Routine'] = self.routine_duration * 60
        self.data_days = days_data
        self.cached = True

    def pie_chart(self, interval=None, level=0, dst_fname=None, dpi=200,
                  display_time_thief=True,
                  display_routine=True):
        """ display pie chart

        interval: 统计周期，tuple 类型数据，其中 interval[0] 表示开始的日期，interval[1] 表示结束日期
        level: 目前只支持 0 或 1。0 表示顶层分类，1 表示自定义的标签
        display_time_thief: 是否显示时间小偷"""

        if not self.cached:
            self._process_data()

        # select data from interval
        if not interval:
            interval = (self.start_day, self.end_day)
        data = self.data_raw.loc[interval[0]: interval[1]]

        # group by List Name
        level1 = data.groupby('List Name').sum()
        explode = None
        _sum = lambda interval, field: np.sum(self.data_days[interval[0]: interval[1]])[field]
        if display_routine:
            routine = pd.DataFrame({'Duration': [_sum(interval, 'Routine')]}, index=['例行公事'])
            level1 = pd.concat([level1, routine])
        if display_time_thief:
            thief = pd.DataFrame({'Duration': [_sum(interval, 'Thief')]}, index=['时间小偷'])
            level1 = pd.concat([level1, thief])
            # highlight time thief
            explode = np.zeros(len(level1['Duration'].values))
            explode[-1] = 0.05

        print level1['Duration']
        print np.sum(level1['Duration'])
        plt.clf()
        _labels = lambda values: [v.decode('utf-8') for v in values]
        title = u'统计周期: [%s - %s]' % (interval[0], interval[1])
        if not display_routine:
            title = title + u' - 例行公事: [%d 小时/天]' % self.routine_duration
        plt.title(title)
        plt.axis('equal')
        plt.pie(level1['Duration'].values, explode=explode, labels=_labels(level1.index.values),
                autopct='%1.0f%%')

        if not dst_fname:
            dst_fname = self.datafile + '.png'
        plt.savefig(dst_fname, dpi=dpi)

    def workload_chart(self, interval=None, dst_fname=None, dpi=200):
        """ 工作量曲线, 主要根据指定周期的工作负荷统计 """
        pass



if __name__ == '__main__':
    log = DidaEventLog('dida_20151220.csv')
    log.pie_chart(display_routine=False)
