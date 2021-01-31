curl -H 'Host: datacenter.eastmoney.com' \
-H 'Origin: null' \
-H 'Accept: application/json, text/plain, */*' \
-H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 13_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 iphonex color=b eastmoney_ios appversion_9.0.3 pkg=com.eastmoney.iphone mainBagVersion=9.0.3 statusBarHeight=44.000000 titleBarHeight=44.000000 density=3.000000 fontsize=2' \
-H 'Accept-Language: zh-cn' \
--compressed 'https://datacenter.eastmoney.com/securities/api/data/get?filter=(SECUCODE%3D%22300058.SZ%22)(REPORT_TYPE%3D%22%E5%B9%B4%E6%8A%A5%22)&client=APP&source=HSF10&type=RPT_F10_FINANCE_MAINFINADATA&sty=APP_F10_MAINFINADATA&ps=5&sr=-1&st=REPORT_DATE'
