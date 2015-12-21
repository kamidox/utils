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

        :param datafile: 数据文件全路径名，数据文件可以从 dida365.com 的设置里导出，是一个 csv 格式的文件
        :param routine_duration: 每天花在其他事情上的平均时长，比如常规的吃喝拉撒睡等，单位小时

        时间黑洞：routine_duration 作为一般性数据输入，便于统计出“时间黑洞”。
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
                    dur *= 60
                return int(dur)
            else:
                return 0

        _date_parser = lambda dstr: pd.Timestamp(dstr).date()

        # real data is from the third line
        raw = pd.read_csv(self.datafile, header=3, index_col='Due Date', parse_dates=True, date_parser=_date_parser)
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

    def _data_from_category(self, field, period):
        data = self.data_raw.loc[period[0]: period[1]]
        top_level_fields = self.data_raw['List Name'].unique()
        if field in top_level_fields:
            d = data[data['List Name'] == field].groupby(level=0).sum()
        else:
            d = data[data['Tag'] == field].groupby(level=0).sum()

        idx = pd.date_range(start=period[0], end=period[1])
        # bug: fillna with 0 will do not draw in the bar chart. So we need fillna with 1
        return d.reindex(idx).fillna(value=1)

    def pie_chart(self, period=None, dst_fname=None, dpi=200,
                  display_time_thief=True,
                  display_routine=False):
        """ 显示时间饼图，重点显示出被“时间黑洞”偷走的时间的百分比。

        :param period: 统计周期，tuple 类型数据，其中 interval[0] 表示开始的日期，interval[1] 表示结束日期
        :param dst_fname: 目标文件名，如果为空，则直接在输出的文件名后加上 ‘_pie_chart.png’ 后缀
        :param dpi: 图片质量
        :param display_routine: 是否显示例行事件的时间及占比
        :param display_time_thief: 是否显示时间小偷"""

        if not self.cached:
            self._process_data()

        # select data from interval
        if not period:
            period = (self.start_day, self.end_day)
        data = self.data_raw.loc[period[0]: period[1]]

        # group by List Name
        level1 = data.groupby('List Name').sum()
        explode = None
        _sum = lambda interval, field: np.sum(self.data_days[interval[0]: interval[1]])[field]
        if display_routine:
            routine = pd.DataFrame({'Duration': [_sum(period, 'Routine')]}, index=['例行公事'])
            level1 = pd.concat([level1, routine])
        if display_time_thief:
            thief = pd.DataFrame({'Duration': [_sum(period, 'Thief')]}, index=['时间黑洞'])
            level1 = pd.concat([level1, thief])
            # highlight time thief
            explode = np.zeros(len(level1['Duration'].values))
            explode[-1] = 0.05

        plt.clf()
        _labels = lambda values: [v.decode('utf-8') for v in values]
        title = u'时间饼图: [%s - %s]' % (period[0], period[1])
        if not display_routine:
            title = title + u' - 例行公事: [%d 小时/天]' % self.routine_duration
        plt.title(title)
        plt.axis('equal')
        plt.pie(level1['Duration'].values, explode=explode, labels=_labels(level1.index.values),
                autopct='%1.0f%%')

        if not dst_fname:
            dst_fname = self.datafile + '_pie_chart.png'
        plt.savefig(dst_fname, dpi=dpi)

    def pie_chart_secondary(self, field, period=None, dst_fname=None, dpi=200):
        """ 显示顶层分类下的子类别的时间饼图，人这个图里可以看到一段时间内, 某个主类别下面的任务的时间分配情况

        :param field: 顶层类别名称
        :param period: 统计周期，tuple 类型数据，其中 interval[0] 表示开始的日期，interval[1] 表示结束日期
        :param dst_fname: 目标文件名，如果为空，则直接在输出的文件名后加上 ‘_pie_chart.png’ 后缀
        :param dpi: 图片质量
        """

        if not self.cached:
            self._process_data()

        if field not in self.data_raw['List Name'].unique():
            print('error: field %s is not an top level category.')
            return

        # select data from interval
        if not period:
            period = (self.start_day, self.end_day)
        data = self.data_raw.loc[period[0]: period[1]]
        tag_list = data.groupby(['List Name', 'Tag']).sum()

        plt.clf()
        _labels = lambda values: [v.decode('utf-8') for v in values]
        title = u'精力分配: %s [%s - %s]' % (field.decode('utf-8'), period[0], period[1])
        plt.title(title)
        plt.axis('equal')
        plt.pie(tag_list.loc[field]['Duration'].values,
                labels=_labels(tag_list.loc[field].index.values),
                autopct='%1.0f%%')

        if not dst_fname:
            dst_fname = self.datafile + '_pie_chart_sec.png'
        plt.savefig(dst_fname, dpi=dpi)

    def workload_chart(self, period=None, dst_fname=None, dpi=200):
        """ 工作量曲线, 显示指定时间周期内的工作量柱状图，可以看一段时间的工作负荷情况及平均值

        :param period: 显示这个时间周期内的工作负荷柱状图
        :param dst_file: 输出的图片文件名，如果没指定，则直接在输入文件名后加 '_workload_chart.png' 后缀
        :param dpi: 图片质量
        """
        if not self.cached:
            self._process_data()

        plt.clf()

        idx = pd.date_range(start=self.start_day, end=self.end_day)
        days = self.data_days.reindex(idx)
        # bug: fillna with 0 will do not draw in the bar chart. So we need fillna with 1
        days.fillna(value=1, inplace=True)

        if not period:
            period = (self.start_day, self.end_day)
        days = days.loc[period[0]: period[1]]

        def _average(p):
            return np.sum(days['Duration']) / (pd.Timestamp(p[1]) - pd.Timestamp(p[0])).days / 60.0

        plt.title(u'工作负荷: [%.02f 小时/天]' % _average(period))
        plt.xticks([])
        plt.xlabel(u'日期: [%s - %s]' % (period[0], period[1]))
        plt.ylabel(u'时长（小时）')
        plt.bar(days.index.values, days['Duration'].values / 60)

        if not dst_fname:
            dst_fname = self.datafile + '_workload_chart.png'
        plt.savefig(dst_fname, dpi=dpi)

    def permanent_action_chart(self, fields=None, period=None, dst_fname=None, dpi=200):
        """ 显示指定时间周期内，指定工作的持续时间投入信息。从这里可以看到我们的持续行动能力。

        :param period: 显示这个时间周期内时间统计信息
        :param fields: 要统计的工作列表。如果没有提供，则直接显示顶层类别的工作时间柱状图。
        :param dst_fname: 目标图表保存的文件名，如果没有提供，则在输入文件后加上 '_pa_chart.png' 后缀。
        :param dpi: 图片质量
        :return: 无
        """
        if not self.cached:
            self._process_data()

        plt.clf()
        if not period:
            period = (self.start_day, self.end_day)

        top_level_fields = self.data_raw['List Name'].unique()
        if not fields:
            fields = top_level_fields

        plt.title(u'持续行动')
        plt.xticks([])
        plt.xlabel(u'日期: [%s - %s]' % (period[0], period[1]))
        plt.ylabel(u'时长（小时）')

        width = 0.8 / len(fields)
        woff = 0
        ci = 0
        colors = ('g', 'y', 'c', 'b', 'r', 'm', 'k')
        for f in fields:
            data = self._data_from_category(f, period)
            idx = np.arange(len(data.index.values))
            plt.bar(idx + woff, data['Duration'].values / 60, width, facecolor=colors[ci])
            woff += width
            ci = (ci + 1) % len(colors)

        def _fieldnames(fns):
            names = [s.decode('utf-8') for s in fns]
            times = [self._data_from_category(f, period)['Duration'].sum() for f in fns]
            return [u'%s - %.02f 小时' % (n, t / 60.0) for n, t in zip(names, times)]

        plt.legend(_fieldnames(fields), loc='best')
        if not dst_fname:
            dst_fname = self.datafile + '_pa_chart.png'
        plt.savefig(dst_fname, dpi=dpi)


if __name__ == '__main__':
    log = DidaEventLog('dida_20151220.csv')
    period = ('2015-12-1', '2015-12-20')
    log.pie_chart(period=period, display_routine=False)
    log.workload_chart(period=period)
    log.pie_chart_secondary('自我成长', period=period)
    #log.permanent_action_chart()
    log.permanent_action_chart(fields=['机器学习', '写作'], period=period)
    #log.permanent_action_chart(fields=['自我提升', '机器学习', '写作'])
