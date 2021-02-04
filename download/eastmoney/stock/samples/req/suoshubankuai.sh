curl -i \
-H 'Host: emh5.eastmoney.com' \
-H 'Content-Type: application/json;charset=utf-8' \
-H 'Origin: null' \
-H 'Accept: application/json, text/plain, */*' \
-H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 13_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 iphonex color=b eastmoney_ios appversion_9.0.3 pkg=com.eastmoney.iphone mainBagVersion=9.0.3 statusBarHeight=44.000000 titleBarHeight=44.000000 density=3.000000 fontsize=2' \
-H 'Cache-Control: public' \
-H 'Accept-Language: zh-cn' \
--data-binary '{"fc":"68829901","platform":"ios","fn":"%E8%93%9D%E8%89%B2%E5%85%89%E6%A0%87","stockMarketID":"0","stockTypeID":"80","color":"b","preload":"1","Sys":"ios","ProductType":"cft","Version":"9.0.3","DeviceType":"iOS 13.4.1","DeviceModel":"iPhone10,3","mobile":"","UniqueID":"B3e615A1F6CA-83E0-4039-98A6-87E4346A4B490a52","mainBagVersion":"9.0.3","bankocr":"1"}' \
--compressed 'https://emh5.eastmoney.com/api/HeXinTiCai/GetSuoShuBanKuai'
