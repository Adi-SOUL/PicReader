# PicReader

![readpic](https://s2.loli.net/2023/01/06/k28jBV4oDxnRY6e.png)

A simple script which can help you read scattered pictures

## How to use

```shell
python3 main.py
```

Make sure you have installed all the required libraries, or you can get releases here:[Releases · Adi-SOUL/PicReader · GitHub](https://github.com/Adi-SOUL/PicReader/releases)

## Functions

### **Use dir**

 choose the directory which contains your scattered pictures

### **Use file**

choose the content file (it will be generated automatically after you choose your directory for the first time.)

### Low Memory Mode

This mode will allow you to use the reader on computers with low RAM.

### Up/Right Keys

To the last picture;

### Down/Left Keys

To the next picture;

### Tab Keys

* *Enter the page number where you want to go, or give the offset.*

        for example, if you were on P20, *+50* will take you to P70 and *-19* will take you to P1.

* *Fast Save*
  
  Save the picture package as a single .db file
  
  **CAUTION: NEVER load files which are from unknown sources sinces we are using dill/pickle module ! ! !**

### Esc Keys

Reload pictures.
