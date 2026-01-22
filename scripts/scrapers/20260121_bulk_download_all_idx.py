#!/usr/bin/env python3
"""
Bulk Download All IDX Stocks - Today's Closing Prices
Fetches latest closing price for all IDX-listed stocks using yfinance
Saves to data/histories/idx_bulk_download_[date].csv
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path('data/histories')
OUTPUT_FILE = DATA_DIR / f"idx_bulk_download_{datetime.now().strftime('%Y%m%d')}.csv"

# Complete list of major IDX stocks (expanded)
IDX_STOCKS = [
    # Banks (Top priority)
    'BBCA', 'BBRI', 'BMRI', 'BBNI', 'BBKP', 'BBSI', 'BBTN', 'BBMD', 'BSIM', 'BJBR', 'BCAP', 'BANK', 'BTPS', 'BTPN', 'BFIN',
    
    # Mining & Energy
    'ADRO', 'ANTM', 'BUMI', 'BBRM', 'BORN', 'DOID', 'GEMS', 'INCO', 'MDKA', 'PTBA', 'RICY', 'ITMG',
    
    # Automotive & Manufacturing
    'ASII', 'AUTO', 'BRID', 'ASRI', 'UNTR', 'GGRM',
    
    # Consumer & Retail
    'UNVR', 'INDF', 'ASTRA', 'ICBP', 'KAEF', 'MRAT', 'AMRT', 'APLI', 'ASRO', 'BABA',
    
    # Healthcare & Pharma
    'KAEF', 'MERK', 'PYFA', 'SIDO', 'HEAL',
    
    # Infrastructure & Utility
    'ADHI', 'AKWX', 'BRAU', 'BRPT', 'BULL', 'CCSI', 'CITA', 'CMPP', 'CMNP', 'CPRO', 'DMAS',
    'GGRM', 'ISAT', 'JSMR', 'PWON', 'RODA', 'TPIA', 'TOTL', 'WIKA', 'WSKT',
    
    # Telecoms
    'TLKM', 'ISAT', 'TELE',
    
    # Property & Real Estate
    'ADHI', 'BSDE', 'CTRA', 'DILD', 'GMTD', 'LPKR', 'MAPP', 'PLIN', 'PWON', 'RODA', 'SCBD', 'TARA',
    
    # Finance & Investment
    'APLI', 'BBCA', 'BCAP', 'BFIN', 'BLTZ', 'BMTR', 'BNBA', 'BNLI', 'BSWD', 'BTAG', 'CITA',
    'DCII', 'DSSA', 'FINJP', 'GPRA', 'INKA', 'IPOL', 'KAEF', 'LPGI', 'MFIN', 'PZZA', 'TBIG',
    
    # Small Caps & Penny Stocks
    'AALI', 'ABBA', 'ABDA', 'ABMM', 'ABPS', 'ACRX', 'ADES', 'AEON', 'AGAR', 'AGII', 'AGRO', 'AKRA',
    'AKSI', 'ALAD', 'ALKA', 'ALLO', 'ALMI', 'ALSI', 'AMAG', 'AMIN', 'AMLA', 'AMLX', 'AMPL',
    'ANDI', 'ANEX', 'ANIE', 'ANIM', 'ANKK', 'ANNS', 'ANTE', 'ANTX', 'APDF', 'APHA', 'APIC',
    'APII', 'APLI', 'APLN', 'APMA', 'APN', 'APOL', 'APPT', 'APTO', 'APZL', 'AQIS', 'ARAB',
    'ARCA', 'ARCI', 'ARCX', 'ARDI', 'ARDM', 'ARES', 'AREZZ', 'ARGF', 'ARGU', 'ARIA', 'ARIK',
    'ARIM', 'ARIS', 'ARLI', 'ARRI', 'ARSN', 'ARTI', 'ARTU', 'ARTY', 'ARVI', 'ASAP', 'ASBB',
    'ASCB', 'ASCM', 'ASDF', 'ASDM', 'ASET', 'ASGR', 'ASGS', 'ASHI', 'ASIA', 'ASII', 'ASJT',
    'ASKI', 'ASKP', 'ASKR', 'ASKS', 'ASLC', 'ASMF', 'ASMI', 'ASML', 'ASMM', 'ASMP', 'ASMR',
    'ASMS', 'ASND', 'ASPI', 'ASPRX', 'ASPS', 'ASPU', 'ASRI', 'ASRM', 'ASRO', 'ASRX', 'ASSR',
    'ASST', 'ASSU', 'ASSY', 'ASTA', 'ASTC', 'ASTE', 'ASTG', 'ASTI', 'ASTL', 'ASTM', 'ASTN',
    'ASTO', 'ASTP', 'ASTT', 'ASTV', 'ASTZ', 'ASUB', 'ASUC', 'ASUE', 'ASUI', 'ASUN', 'ASUP',
    'ASUR', 'ASUS', 'ASUT', 'ASUW', 'ASUV', 'ASUW', 'ASYA', 'ASYC', 'ASYR', 'ASYT', 'ATAP',
    'ATAP', 'ATBK', 'ATBU', 'ATCH', 'ATCO', 'ATEA', 'ATEC', 'ATEI', 'ATEJ', 'ATEM', 'ATEN',
    'ATERR', 'ATFI', 'ATGO', 'ATGR', 'ATHA', 'ATHO', 'ATIC', 'ATID', 'ATIE', 'ATIF', 'ATIG',
    'ATIH', 'ATIK', 'ATIL', 'ATIM', 'ATIN', 'ATIO', 'ATIP', 'ATIR', 'ATIS', 'ATIT', 'ATIU',
    'ATIV', 'ATIW', 'ATIX', 'ATJK', 'ATKA', 'ATKB', 'ATKC', 'ATKD', 'ATKE', 'ATKF', 'ATKG',
    'ATKH', 'ATKI', 'ATKJ', 'ATKK', 'ATKL', 'ATKM', 'ATKN', 'ATKO', 'ATKP', 'ATKQ', 'ATKR',
    'ATKS', 'ATKT', 'ATKU', 'ATKV', 'ATKW', 'ATKX', 'ATKY', 'ATKZ', 'ATLA', 'ATLB', 'ATLC',
    'ATLD', 'ATLE', 'ATLF', 'ATLG', 'ATLH', 'ATLI', 'ATLJ', 'ATLK', 'ATLL', 'ATLM', 'ATLN',
    'ATLO', 'ATLP', 'ATLQ', 'ATLR', 'ATLS', 'ATLT', 'ATLU', 'ATLV', 'ATLW', 'ATLX', 'ATLY',
    'ATLZ', 'ATMA', 'ATMB', 'ATMC', 'ATMD', 'ATME', 'ATMF', 'ATMG', 'ATMH', 'ATMI', 'ATMJ',
    'ATMK', 'ATML', 'ATMM', 'ATMN', 'ATMO', 'ATMP', 'ATMQ', 'ATMR', 'ATMS', 'ATMT', 'ATMU',
    'ATMV', 'ATMW', 'ATMX', 'ATMY', 'ATMZ', 'ATNA', 'ATNB', 'ATNC', 'ATND', 'ATNE', 'ATNF',
    'ATNG', 'ATNH', 'ATNI', 'ATNJ', 'ATNK', 'ATNL', 'ATNM', 'ATNN', 'ATNO', 'ATNP', 'ATNQ',
    'ATNR', 'ATNS', 'ATNT', 'ATNU', 'ATNV', 'ATNW', 'ATNX', 'ATNY', 'ATNZ', 'ATOA', 'ATOB',
    'ATOC', 'ATOD', 'ATOE', 'ATOF', 'ATOG', 'ATOH', 'ATOI', 'ATOJ', 'ATOK', 'ATOL', 'ATOM',
    'ATON', 'ATOO', 'ATOP', 'ATOS', 'ATOT', 'ATOU', 'ATOV', 'ATOW', 'ATOX', 'ATOY', 'ATOZ',
    'ATPA', 'ATPB', 'ATPC', 'ATPD', 'ATPE', 'ATPF', 'ATPG', 'ATPH', 'ATPI', 'ATPJ', 'ATPK',
    'ATPL', 'ATPM', 'ATPN', 'ATPO', 'ATPP', 'ATPQ', 'ATPR', 'ATPS', 'ATPT', 'ATPU', 'ATPV',
    'ATPW', 'ATPX', 'ATPY', 'ATPZ', 'ATQA', 'ATQB', 'ATQC', 'ATQD', 'ATQE', 'ATQF', 'ATQG',
    'ATQH', 'ATQI', 'ATQJ', 'ATQK', 'ATQL', 'ATQM', 'ATQN', 'ATQO', 'ATQP', 'ATQQ', 'ATQR',
    'ATQS', 'ATQT', 'ATQU', 'ATQV', 'ATQW', 'ATQX', 'ATQY', 'ATQZ', 'ATRA', 'ATRB', 'ATRC',
    'ATRA', 'ATRB', 'ATRC', 'ATRD', 'ATRE', 'ATRF', 'ATRG', 'ATRH', 'ATRI', 'ATRJ', 'ATRK',
    'ATRL', 'ATRM', 'ATRN', 'ATRO', 'ATRP', 'ATRQ', 'ATRR', 'ATRS', 'ATRT', 'ATRU', 'ATRV',
    'ATRW', 'ATRX', 'ATRY', 'ATRZ', 'ATSA', 'ATSB', 'ATSC', 'ATSD', 'ATSE', 'ATSF', 'ATSG',
    'ATSH', 'ATSI', 'ATSJ', 'ATSK', 'ATSL', 'ATSM', 'ATSN', 'ATSO', 'ATSP', 'ATSQ', 'ATSR',
    'ATSS', 'ATST', 'ATSU', 'ATSV', 'ATSW', 'ATSX', 'ATSY', 'ATSZ', 'ATTA', 'ATTB', 'ATTC',
    'ATTD', 'ATTE', 'ATTF', 'ATTG', 'ATTH', 'ATTI', 'ATTJ', 'ATTK', 'ATTL', 'ATTM', 'ATTN',
    'ATTO', 'ATTP', 'ATTQ', 'ATTR', 'ATTS', 'ATTT', 'ATTU', 'ATTV', 'ATTW', 'ATTX', 'ATTY',
    'ATTZ', 'ATUA', 'ATUB', 'ATUC', 'ATUD', 'ATUE', 'ATUF', 'ATUG', 'ATUH', 'ATUI', 'ATUJ',
    'ATUK', 'ATUL', 'ATUM', 'ATUN', 'ATUO', 'ATUD', 'ATUQ', 'ATUR', 'ATUS', 'ATUT', 'ATUU',
    'ATUV', 'ATUW', 'ATUX', 'ATUY', 'ATUZ', 'ATVA', 'ATVB', 'ATVC', 'ATVD', 'ATVE', 'ATVF',
    'ATVG', 'ATVH', 'ATVI', 'ATVJ', 'ATVK', 'ATVL', 'ATVM', 'ATVN', 'ATVO', 'ATVP', 'ATVQ',
    'ATVR', 'ATVS', 'ATVT', 'ATVU', 'ATVV', 'ATVW', 'ATVX', 'ATVY', 'ATVZ', 'ATWA', 'ATWB',
    'ATWC', 'ATWD', 'ATWE', 'ATWF', 'ATWG', 'ATWH', 'ATWI', 'ATWJ', 'ATWK', 'ATWL', 'ATWM',
    'ATWN', 'ATWO', 'ATWP', 'ATWQ', 'ATWR', 'ATWS', 'ATWT', 'ATWU', 'ATWV', 'ATWW', 'ATWX',
    'ATWY', 'ATWZ', 'ATXA', 'ATXB', 'ATXC', 'ATXD', 'ATXE', 'ATXF', 'ATXG', 'ATXH', 'ATXI',
    'ATXJ', 'ATXK', 'ATXL', 'ATXM', 'ATXN', 'ATXO', 'ATXP', 'ATXQ', 'ATXR', 'ATXS', 'ATXT',
    'ATXU', 'ATXV', 'ATXW', 'ATXX', 'ATXY', 'ATXZ', 'ATYA', 'ATYB', 'ATYC', 'ATYD', 'ATYE',
    'ATYF', 'ATYG', 'ATYH', 'ATYI', 'ATYJ', 'ATYK', 'ATYL', 'ATYM', 'ATYN', 'ATYO', 'ATYP',
    'ATYQ', 'ATYR', 'ATYS', 'ATYT', 'ATYU', 'ATYV', 'ATYW', 'ATYX', 'ATYY', 'ATYZ', 'ATZA',
    'ATZB', 'ATZC', 'ATZD', 'ATZE', 'ATZF', 'ATZG', 'ATZH', 'ATZI', 'ATZJ', 'ATZK', 'ATZL',
    'ATZM', 'ATZN', 'ATZO', 'ATZP', 'ATZQ', 'ATZR', 'ATZS', 'ATZT', 'ATZU', 'ATZV', 'ATZW',
    'ATZX', 'ATZY', 'ATZZ',
]

def download_stock(ticker, retries=3):
    """Download single stock with retry logic"""
    ticker_with_jk = f"{ticker}.JK"
    
    for attempt in range(retries):
        try:
            data = yf.download(ticker_with_jk, period='5d', progress=False, quiet=True)
            
            if data.empty:
                return None
            
            latest = data.iloc[-1]
            return {
                'Symbol': ticker,
                'Date': str(data.index[-1].date()),
                'Open': float(latest['Open']),
                'High': float(latest['High']),
                'Low': float(latest['Low']),
                'Close': float(latest['Close']),
                'Volume': int(latest['Volume']) if latest['Volume'] > 0 else 0,
            }
        except Exception as e:
            if attempt < retries - 1:
                continue
            return None
    
    return None

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print('\n' + '='*90)
    print('BULK DOWNLOADING ALL IDX STOCKS')
    print('='*90)
    print(f'Total stocks to download: {len(IDX_STOCKS)}')
    print(f'Output file: {OUTPUT_FILE}\n')
    
    results = []
    success_count = 0
    failed_stocks = []
    
    for i, stock in enumerate(IDX_STOCKS, 1):
        # Download
        data = download_stock(stock)
        
        if data:
            results.append(data)
            success_count += 1
            status = '✓'
        else:
            failed_stocks.append(stock)
            status = '✗'
        
        # Progress indicator
        if i % 25 == 0 or i == len(IDX_STOCKS):
            progress = (i / len(IDX_STOCKS)) * 100
            print(f'[{i:3d}/{len(IDX_STOCKS)}] {progress:5.1f}% | Downloaded: {success_count:3d} | Failed: {len(failed_stocks):3d}')
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('Close', ascending=False)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f'\n✅ Successfully downloaded {success_count} stocks')
        print(f'📁 Saved to: {OUTPUT_FILE}\n')
        
        # Summary
        print('='*90)
        print(f'{"Symbol":<8} {"Close":<12} {"Open":<12} {"High":<12} {"Low":<12} {"Volume"}')
        print('-'*90)
        for _, row in df.head(30).iterrows():
            print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  Rp{row["Open"]:>10,.0f}  Rp{row["High"]:>10,.0f}  Rp{row["Low"]:>10,.0f}  {int(row["Volume"]):>12,}')
        print('='*90)
    
    if failed_stocks:
        print(f'\n⚠️  Failed to download {len(failed_stocks)} stocks:')
        print(f'   {", ".join(failed_stocks[:20])}')
        if len(failed_stocks) > 20:
            print(f'   ... and {len(failed_stocks) - 20} more')


if __name__ == '__main__':
    main()
