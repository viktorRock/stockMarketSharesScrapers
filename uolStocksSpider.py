import scrapy
import datetime
import re
import urllib
import sys
class uolStocksSpider(scrapy.Spider):
    name = 'uolStocksSpider'


    def __init__(self, category=None, *args, **kwargs):
        super(uolStocksSpider, self).__init__(*args, **kwargs)
        target_url = 'http://cotacoes.economia.uol.com.br/acao/cotacoes-historicas.html?'

        #attrs
        stocks = str(getattr(self, 'stock', 'PETR4'))
        size = 'size=' + getattr(self,'rows','10') + '&'
        page ='page=' + getattr(self,'page','1') + '&'
        fileMode =getattr(self,'fileMode',False)
        postStocks = size + page + 'period='

        #self.stocks = stocks.split(',')
        self.stocks = re.findall(r"[\w']+", stocks)
        for stock in self.stocks:
            stocksUrl = 'codigo=' + stock + '.SA&'
            url = target_url + stocksUrl + postStocks
            self.start_urls.append(url)

        #self.start_urls = [url]
        self.fileMode = fileMode

    def parse(self, response, findCriteria = 'td :: text'):
        ##teste
        print ('SYSversion = ' + str(sys.version))
        headerList = response.css('table.tblCotacoes').css('th::text').extract()

        #check python version
        if sys.version_info >= (3,6):
            urlsplit = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(response.url).query))
        else:
            print('parse != 3,6' + '\n')
            from urlparse import parse_qs, urlparse
            urlsplit = dict(parse_qs(urlparse(response.url).query))

        #print('urlsplit = ' + str(urlsplit) + '\n')
        curStock = urlsplit['codigo']
        ultimaCotData = response.css('p.data').css('p::text').extract_first()
        primeiraData = response.css('table.tblCotacoes').css('tr').css('td ::text').extract_first()

        if ultimaCotData is None:
            yield {'stock': curStock, 'alerta': True}
        else:
            try:
                 ultimaCotData = datetime.datetime.strptime(ultimaCotData, "%d %b. %Y").date()
            except:
                # Portuguese locale
                print('ultimaCotData = ' + ultimaCotData + '\n')
                brMonthsDict = {'Fev':'Feb','Abr':'Apr','Ago':'Aug','Out':'Oc','Dez':'Dec'}
                for key in brMonthsDict.keys():
                    ultimaCotData = ultimaCotData.replace(key, brMonthsDict[key])
                ultimaCotData = datetime.datetime.strptime(ultimaCotData, "%d %b. %Y").date()
            primeiraData = datetime.datetime.strptime(primeiraData, "%d/%m/%Y").date()

        if self.fileMode:
            outFilename = (curStock) + "_" + str(datetime.date.today()) + ".txt"
            outFile = open(outFilename, "w")
            outFile.write(str(response.css('title::text').extract_first()) + '\n')
            outFile.write(str(headerList) + '\n')

        #ultimaCotData != primeiraData:
        if ultimaCotData != primeiraData:
            ultimaCotHeader = response.css('div#infoTable').css('th::text').extract()
            del ultimaCotHeader[0]
            ultimaCotValues = response.css('tr.baixa').css('td::text').extract()
            ultimaCotValues = ultimaCotValues + response.css('tr.alta').css('td::text').extract()
            ultimaCotValuesList = [ultimaCotData.strftime("%d/%m/%Y"), ultimaCotValues[3], ultimaCotValues[5], ultimaCotValues[4], ultimaCotValues[1], ultimaCotValues[2], ultimaCotValues[7]]
            ultimaCotDict = dict(zip(headerList, ultimaCotValuesList))
            ultimaCotDict['stock'] = curStock
            #updating Keys
            print ('ultimaCotDict = ' + str(ultimaCotDict))
            if self.fileMode:
                outFile.write(str(ultimaCotDict.values()) + '\n')
            yield ultimaCotDict

        for title in response.css('table.tblCotacoes').css('tr'):
            line = title.css('td ::text').extract()
            if not line:
                continue
            stockDict = dict(zip(headerList, line))
            stockDict['stock'] = curStock
            yield stockDict
            if self.fileMode:
                outFile.write(str(line) + '\n')
        if self.fileMode:
            outFile.close()

