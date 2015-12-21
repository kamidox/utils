# utils
My utilities codes. Mainly for improve my efficiency in work.

## 时间事件日志

从 dida365.com 导出按照规范记录的时间事件日志，生成统计图表，找出`我的时间去了哪儿`的答案。

### 使用方法

#### 步骤一：利用 dida365 记录时间事件日志

像平常一样在 dida365 上完成 GTD 工作，在记录事件时注意以下规则，用来增加子类别和记录事件的时间。

* dida365 上的`清单`就是我们事件的主类别，可以建立多个清单
* 每个清单的事件标题按照 `[子类别] 事件标题 [时长]` 这样的格式来记录。比如`[写作] 博客《时间事件日志》[1.2h]`。时长支持 `h` 和 `m` ，分别表示小时和分钟
* 给任务分配预期完成时间。统计脚本在统计一个工作在什么时候完成的，是根据预期完成时间来算的，而不是根据点击完成复选框的时间来算的。理由是点击完成的时间是不能变的，比如某个事情忘了记录，过了两天才记录，这个时候点完成，则完成时间是点击完成的那个时间点，而预期完成时间我们可以设置在两天前，这样这项工作就会记录在两天前。

#### 步骤二：导出数据

进入 dida365 的用户`设置`界面，点击`数据备份`，再点击`生成备份`。这一动作会在电脑端保存一份所有你记录在 dida365 上的时间事件日志，这是个 csv 格式的文件。

#### 步骤三：生成统计图表

下载 [Python 统计脚本](https://github.com/kamidox/utils/dida365/dida_event_log.py)。安装 matplotlib, pandas 等必要的库。参考下面的 demo 代码。注释已经把用法写清楚了。

```python
# dida_20151220.csv 是从 dida365.com 上导出的你的时间事件日志，可以取任意你喜欢的文件名
# 用这个文件作为输入，创建时间事件日志对象
# 参数 routine_duration 为每天固定的例行公事时间长度（吃，喝，拉，撒，睡，行，发呆），单位为小时
log = DidaEventLog('dida_20151220.csv', routine_duration=14)
# 设定要统计的时间周期
period = ('2015-12-1', '2015-12-20')
# 生成时间总览饼图
log.pie_chart(period=period, display_routine=False)
# 生成工作负荷图表
log.workload_chart(period=period)
# 生成某个主类别下的子类别的精力分配情况
log.pie_chart_secondary('自我成长', period=period)
# 生成某个类别的时间投入情况，fields 参数可以是主类别也可以是子类别
log.permanent_action_chart(fields=['机器学习', '写作'], period=period)
```

### 参数说明

* **时间黑洞**
  那些发呆走神，刷微博微信的时间就是黑洞时间。我们要想办法把时间黑洞降到 20% 以下。那些为自己理想打着鸡血，走在万众创业路上的同学，估计时间黑洞会为负数。为什么呢？因为他们牺牲了吃喝拉撒睡等例行公事的时间，想着每天要睡够 7 小时，结果只有 5 小时。
* **例行公事**
  我们要睡觉，交通也要花时间，吃饭也要花时间。这部分我们称为例行公事，每天相对比较固定，简单起见，统计时，我们就取个固定值。


### 效果图

**时间总览**

![时间总览](https://raw.githubusercontent.com/kamidox/blogs/master/images/dida365_pie_chart.png)

从这个图表可以清晰地看到 dida365 里面各个顶层类别事件的时间分配。看看那个**时间黑洞**，那些就是被偷走的时间。

**工作负荷**

![工作负荷](https://raw.githubusercontent.com/kamidox/blogs/master/images/dida365_workload_chart.png)

从时间维度查看我们的工作负荷。一目了然。

**精力分配**

![工作负荷](https://raw.githubusercontent.com/kamidox/blogs/master/images/dida365_pie_chart_sec.png)

顶层事件类型下可以有事件子类别，从精力分配图可以清晰地看出来我们的时间花在哪些事情上了。

**持续行动**

![持续行动](https://raw.githubusercontent.com/kamidox/blogs/master/images/dida365_pa_chart.png)

选定我们感兴趣的事件类型，我们可以查看一定周期内，我们的精力投入情况。监督自己持续行动。
