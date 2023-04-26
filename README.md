# reADpIc
 ![readpic](https://s2.loli.net/2023/01/06/k28jBV4oDxnRY6e.png)
## I. 简介
一个帮助你阅读分散图包的软件，同时支持一系列额外功能。
## II. 安装
v1.1版本（以及之后的版本）由于添加了```CLIP```功能，可执行文件打包过程需要打包```torch```依赖，导致超过GitHub的releases上传大小上限。故从**v.1.1版本后**不再在GitHub上提供打包后的可执行文件。（网盘文件：[百度网盘](https://pan.baidu.com/s/1cNXW4_kHH8plHr3dIa6Qeg?pwd=uqn8), 如无法使用，可以联系作者：adijnnuuy@gmail.com）

### 2.1 使用Conda（可选，推荐）：
1. 从[这里](https://www.anaconda.com/)下载并安装Anaconda；
2. （如果你是第一次使用Conda）初始化Conda：
    ```powershell
    conda init
    ```
3. 从conda创建环境：
    ```powershell
    conda create -n reADpIc python=3.11
    ```
4. 使用```pip```安装环境（使用Conda直接安装环境会导致后续可能的打包失败）：
    ```powershell
    conda activate reADpIc
    pip install -r requirements.txt
    ```
5. 运行：
    ```powershell
    python reader.py
    ```
6. （可能的）```torch```安装失败：

   如果```torch```不能正确识别GPU设备，请检查自身```cuda```以及```cudnn```安装情况，并从[这里](https://pytorch.org/get-started/previous-versions/)查找适合的```torch```版本，然后使用
   ```powershell
   pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117
   ```
### 2.2 不使用Conda（不推荐）：
1. 安装Python：

   [Python 官网](https://www.python.org/downloads/)

   [Python 安装](https://www.tutorialspoint.com/how-to-install-python-in-windows)

2. 创建[虚拟环境](https://docs.python.org/3/library/venv.html)；

后续和2.2.4一致。

### 2.3 打包可执行文件：
如果你想打包可执行文件的话：
1. 安装```pyinstaller```:
   ```powershell
   pip install pyinstaller
   ```
2. 打包文件：
   ```powershell
   pyinstaller -w reader.py -n reADpIc -i="PicReader.ico" --add-data "PicReader.ico:."
   ```
3. （如有）```clip_cn```文件缺失，将python环境中的```clip_cn```文件夹复制到```reADpIc```文件夹下。
   
## III. 功能介绍

```With File```按钮可以让你打开```.db```，```.dbx```（v1.1版本之后），```.png```，```.jpg```，```.jpeg```文件；

```With Dir```按钮可以让你打开图片所在文件夹；

```Low Memory Mode```：对于内存较少的用户，打开后无法将图片保存为```.db```，```.dbx```（v1.1版本之后）文件，但是允许阅读大体积文件夹。 当用户内存**小于等于16GB**时自动开启，可视情况手动关闭。

### 3.1 功能按键：
1. ```方向键```： 

   ⬅️⬆️：切换到上一张图片；

   ⬇️➡️：切换到下一张图片；

2. ```滚轮```： 切换浏览侧边栏图片；*侧边栏可以通过左上角按钮折叠与展开；*
3. ```CTRL+滚轮```：缩放图片；
4. ```鼠标左键```：拖拽图片。
### 3.2 扩展：
1. ```.db```（v1.2及之后弃用）与```.dbx```（v1.1版本之后）文件支持：

   点击工具栏上的```Files -> Fast Save```可以将当前阅读内容转换为```.db```文件；

   点击工具栏上的```Files -> Fast Save(Full size)```可以将当前阅读内容转换为```.dbx```文件；

   ```.db```与```.dbx```文件可以帮助你存放图片文件，在本软件中有更快的加载速度（相较于从文件夹读取）。与```.db```不同，```.dbx```在保存时不会更改图片的分辨率。

   点击工具栏上的```Files -> Get Back Pictures```可以将```.db```与```.dbx```（v1.1版本之后）文件转换为图片内容。
   
   ‼️自v1.2后```.dbx```文件会采用新的保存方式，从而避免pickle库序列化的文件不安全且磁盘占用过大的问题，如果你有v1.2之前保存的```.db```或```.dbx```文件，请使用历史版本将其转换为原始图片文件。

2. ```.psd```文件支持：

   点击工具栏上的```Files -> Convert Files -> PSD/Dir to PNG```，可以把```.psd```文件（批量）导出为```.png```文件，（虽然挺慢的）。不需要安装Adobe Photoshop。
   
   *tools.\_\_init\_\_.discarded_layers中放入你不想被导出的图层名字（打包前有效）*   

3. ```.gif```文件支持：

   点击工具栏上的```Tools -> GIF Reader```打开```.gif```文件阅读器。

4. ```Tools -> Jump to```页面跳转：

   输入数字：跳转到指定页数；

   输入偏差：向前（后）跳转页数。```+10```：向后10页；```-10```：向前10页

### 3.3 其他：
1. 主题风格切换；

   点击工具栏上的```Tools -> Themes```切换主题；

2. 触摸屏支持。

   点击工具栏上的```Tools -> Touch```唤起小组件；

3. ```CILP```支持：

   点击工具栏上的```Tools -> Sorter```唤起小组件，输入关键字后，会自动按照关键词相似度对图片进行排序。

4. 内存监视：

   点击工具栏上的```Tools -> Mem Monitor```唤起小组件，用于查看当前电脑内存使用情况。

5. 重新加载：

   点击工具栏上的```Files -> Reload```重新从文件或文件夹加载图片。


## 特别感谢
[CLIP_CN](https://github.com/OFA-Sys/Chinese-CLIP) ⬅️ 提供了```tools.tools.clip_sort```的支持

[ChatGPT](https://chat.openai.com) ⬅️ 他帮我处理了```tools.tools.find_longest_common_prefix```

[ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) ⬅️ UI美化
