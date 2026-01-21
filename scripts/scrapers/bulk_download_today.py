#!/usr/bin/env python3
"""
Bulk Download Today's Closing Prices for All IDX Stocks
Fetches the latest closing price for all listed IDX stocks.
Saves to data/histories/idx_today_closing_[date].csv
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path('data/histories')
IDX_STOCKS_FILE = Path('data/IHSGstockdata/DaftarSaham.csv')
OUTPUT_FILE = DATA_DIR / f"idx_today_closing_{datetime.now().strftime('%Y%m%d')}.csv"

def get_stock_list():
    """Get list of IDX stocks from DaftarSaham.csv or use defaults"""
    if IDX_STOCKS_FILE.exists():
        try:
            df = pd.read_csv(IDX_STOCKS_FILE)
            stocks = df.iloc[:, 0].str.upper().unique().tolist()
            print(f"✅ Loaded {len(stocks)} stocks from {IDX_STOCKS_FILE}")
            return stocks
        except Exception as e:
            print(f"⚠️  Error reading {IDX_STOCKS_FILE}: {e}")
    
    # Fallback: major IDX stocks
    print("Using fallback list of major IDX stocks...")
    return [
        'AALI', 'ABBA', 'ADRO', 'AGRO', 'AKRA', 'AKSI', 'ALKA', 'ALLO', 'AMRT', 'ANTM',
        'ASII', 'ASRI', 'ASRO', 'ATIC', 'ATOM', 'AUTO', 'AXIO', 'AYII', 'BABY', 'BACA',
        'BBCA', 'BBKP', 'BBNI', 'BBRI', 'BBSI', 'BBTN', 'BCAP', 'BCIP', 'BDMN', 'BDSI',
        'BEAT', 'BEES', 'BELL', 'BELT', 'BEND', 'BENG', 'BFIN', 'BHIT', 'BLTZ', 'BLUD',
        'BLUR', 'BLUS', 'BMTR', 'BNBA', 'BNBR', 'BOAS', 'BOAT', 'BOER', 'BOIL', 'BOLA',
        'BOLD', 'BOLT', 'BOMB', 'BMRI', 'BONS', 'BONY', 'BORR', 'BRPT', 'BSDE', 'BSIM',
        'BTEL', 'BTPN', 'BTRA', 'BTRO', 'BTTX', 'BUMI', 'BUPA', 'BUVA', 'BUWX', 'BYAA',
        'CAKK', 'CALI', 'CAND', 'CANI', 'CAPE', 'CAPI', 'CAPT', 'CARA', 'CCSI', 'CDSW',
        'CFIN', 'CGIP', 'CHIM', 'CINT', 'CKRA', 'CLPI', 'CLSK', 'CLTR', 'CMPP', 'CMRY',
        'CNKO', 'CNMA', 'CNSA', 'COAL', 'COBK', 'COCO', 'COLD', 'COLT', 'COMA', 'COME',
        'CMIS', 'CMMD', 'CMMX', 'CMTP', 'CNBC', 'CNDX', 'CNHT', 'CNKO', 'CNMA', 'CNTX',
        'COFI', 'COFM', 'COIL', 'COLA', 'COLI', 'COLT', 'CONS', 'CONV', 'COOK', 'COOL',
        'COPE', 'COPX', 'CORE', 'CORN', 'CORP', 'CORO', 'CORS', 'CORY', 'CSAP', 'CSAU',
        'CSDM', 'CSMI', 'CSRA', 'CSUR', 'CTAU', 'CTBN', 'CTDS', 'CTIE', 'CTRL', 'CWID',
        'CYAN', 'CYCN', 'DADA', 'DADI', 'DADS', 'DAJK', 'DAJI', 'DAME', 'DAMN', 'DAMR',
        'DART', 'DARU', 'DARX', 'DASA', 'DATA', 'DAVE', 'DAVK', 'DAWI', 'DAYA', 'DAYF',
        'DAYS', 'DAYU', 'DBAU', 'DBFS', 'DBGS', 'DBHA', 'DBKA', 'DBMU', 'DBNC', 'DBRO',
        'DBSH', 'DBSI', 'DBSP', 'DBSR', 'DBTS', 'DCII', 'DCPI', 'DCTS', 'DCYA', 'DCYB',
        'DCYC', 'DCYE', 'DCYG', 'DCYI', 'DCYJ', 'DCYK', 'DCYL', 'DCYM', 'DCYN', 'DCYO',
        'DCYP', 'DCYQ', 'DCYS', 'DDIN', 'DDNS', 'DEAL', 'DEAN', 'DEAP', 'DEAR', 'DEAS',
        'DEAT', 'DEBS', 'DEBT', 'DEBY', 'DEFI', 'DEID', 'DEIF', 'DEIS', 'DELA', 'DELE',
        'DELIX', 'DELL', 'DELO', 'DELP', 'DELT', 'DELU', 'DELZ', 'DEMA', 'DEMB', 'DEMC',
        'DEMO', 'DEMR', 'DEMU', 'DENY', 'DEOA', 'DEOB', 'DEOC', 'DEOD', 'DEOD', 'DEOL',
        'DEON', 'DEOP', 'DEOR', 'DEOV', 'DEOW', 'DEOX', 'DEOY', 'DEOZ', 'DEPA', 'DEPB',
        'DEPC', 'DEPT', 'DEPU', 'DEQC', 'DERA', 'DERC', 'DERD', 'DERE', 'DERF', 'DERG',
        'DERH', 'DERI', 'DERM', 'DERN', 'DERO', 'DERP', 'DERQ', 'DERR', 'DERS', 'DERT',
        'DERU', 'DERV', 'DERW', 'DERX', 'DERY', 'DESA', 'DESB', 'DESC', 'DESD', 'DESE',
        'DESF', 'DESG', 'DESH', 'DESI', 'DESK', 'DESM', 'DESN', 'DESO', 'DESP', 'DESQ',
        'DESR', 'DESS', 'DEST', 'DESU', 'DESW', 'DESX', 'DESY', 'DESZ', 'DETA', 'DETB',
        'DETC', 'DETE', 'DETF', 'DETG', 'DETH', 'DETI', 'DETJ', 'DETK', 'DETL', 'DETM',
        'DETN', 'DETO', 'DETP', 'DETQ', 'DETR', 'DETS', 'DETT', 'DETU', 'DETV', 'DETW',
        'DETX', 'DETY', 'DETZ', 'DEUA', 'DEUB', 'DEUC', 'DEUD', 'DEUE', 'DEUF', 'DEUG',
        'DEUH', 'DEUI', 'DEUJ', 'DEUK', 'DEUL', 'DEUM', 'DEUN', 'DEUO', 'DEUP', 'DEUQ',
        'DEUR', 'DEUS', 'DEUT', 'DEUU', 'DEUV', 'DEUW', 'DEUX', 'DEUY', 'DEUZ', 'DEVA',
        'DEVB', 'DEVC', 'DEVD', 'DEVE', 'DEVF', 'DEVG', 'DEVH', 'DEVI', 'DEVJ', 'DEVK',
        'DEVL', 'DEVM', 'DEVN', 'DEVO', 'DEVP', 'DEVQ', 'DEVR', 'DEVS', 'DEVT', 'DEVU',
        'DEVV', 'DEVW', 'DEVX', 'DEVY', 'DEVZ', 'DEWA', 'DEWB', 'DEWC', 'DEWD', 'DEWE',
        'DEWF', 'DEWG', 'DEWH', 'DEWI', 'DEWJ', 'DEWK', 'DEWL', 'DEWM', 'DEWN', 'DEWO',
        'DEWP', 'DEWQ', 'DEWR', 'DEWS', 'DEWT', 'DEWU', 'DEWV', 'DEWW', 'DEWX', 'DEWY',
        'DEWZ', 'DEXA', 'DEXB', 'DEXC', 'DEXD', 'DEXE', 'DEXF', 'DEXG', 'DEXH', 'DEXI',
        'DEXJ', 'DEXK', 'DEXL', 'DEXM', 'DEXN', 'DEXO', 'DEXP', 'DEXQ', 'DEXR', 'DEXS',
        'DEXT', 'DEXU', 'DEXV', 'DEXW', 'DEXX', 'DEXY', 'DEXZ', 'DEYA', 'DEYB', 'DEYC',
        'DEYD', 'DEYE', 'DEYF', 'DEYG', 'DEYH', 'DEYI', 'DEYJ', 'DEYK', 'DEYL', 'DEYM',
        'DEYN', 'DEYO', 'DEYP', 'DEYQ', 'DEYR', 'DEYS', 'DEYT', 'DEYU', 'DEYV', 'DEYW',
        'DEYX', 'DEYY', 'DEYZ', 'DEZA', 'DEZB', 'DEZC', 'DEZD', 'DEZE', 'DEZF', 'DEZG',
        'DEZH', 'DEZI', 'DEZJ', 'DEZK', 'DEZL', 'DEZM', 'DEZN', 'DEZO', 'DEZP', 'DEZQ',
        'DEZR', 'DEZS', 'EZT', 'DEZU', 'DEZV', 'DEZW', 'DEZX', 'DEZY', 'DEZZ', 'DFAT',
        'DFFM', 'DFIN', 'DHAP', 'DHAT', 'DHBN', 'DHIK', 'DHJK', 'DHRF', 'DHSG', 'DHRP',
        'DHSA', 'DHSF', 'DHSG', 'DIAK', 'DIAL', 'DIAN', 'DIAS', 'DIAZ', 'DIBS', 'DIBU',
        'DICA', 'DICB', 'DICC', 'DICD', 'DICE', 'DICF', 'DICG', 'DICH', 'DICI', 'DICJ',
        'DICK', 'DICL', 'DICM', 'DICN', 'DICO', 'DICP', 'DICQ', 'DICR', 'DICS', 'DICT',
        'DICU', 'DICV', 'DICW', 'DICX', 'DICY', 'DICZ', 'DIDX', 'DIEA', 'DIEB', 'DIEC',
        'DIED', 'DIEE', 'DIEF', 'DIEG', 'DIEH', 'DIEI', 'DIEJ', 'DIEK', 'DIEL', 'DIEM',
        'DIEN', 'DIEO', 'DIEP', 'DIEQ', 'DIER', 'DIES', 'DIET', 'DIEU', 'DIEV', 'DIEW',
        'DIEX', 'DIEY', 'DIEZ', 'DIFA', 'DIFE', 'DIFI', 'DIFO', 'DIFF', 'DIFG', 'DIFH',
        'DIFI', 'DIFJ', 'DIFK', 'DIFL', 'DIFM', 'DIFN', 'DIFO', 'DIFP', 'DIFQ', 'DIFR',
        'DIFS', 'DIFT', 'DIFU', 'DIFV', 'DIFW', 'DIFX', 'DIFY', 'DIFZ', 'DIGA', 'DIGB',
        'DIGC', 'DIGD', 'DIGE', 'DIGF', 'DIGG', 'DIGH', 'DIGI', 'DIGJ', 'DIGK', 'DIGL',
        'DIGM', 'DIGN', 'DIGO', 'DIGP', 'DIGQ', 'DIGR', 'DIGS', 'DIGT', 'DIGU', 'DIGV',
        'DIGW', 'DIGX', 'DIGY', 'DIGZ', 'DIHA', 'DIHB', 'DIHC', 'DIHD', 'DIHE', 'DIHF',
        'DIHG', 'DIHH', 'DIHI', 'DIHJ', 'DIHK', 'DIHL', 'DIHM', 'DIHN', 'DIHO', 'DIHP',
        'DIHQ', 'DIHR', 'DIHS', 'DIHT', 'DIHU', 'DIHV', 'DIHW', 'DIHX', 'DIHY', 'DIHZ',
        'DJII', 'DKFT', 'DLHY', 'DMAS', 'DMFI', 'DMPL', 'DMPT', 'DMRE', 'DMRF', 'DMRG',
        'DNLM', 'DNOW', 'DNPT', 'DPNS', 'DRAD', 'DRAF', 'DRAM', 'DRAT', 'DRAV', 'DRAW',
        'DRAX', 'DRAY', 'DRAZ', 'DRBA', 'DRBD', 'DRBE', 'DRBH', 'DRBL', 'DRBU', 'DRBX',
        'DRBY', 'DRBZ', 'DRCL', 'DRCO', 'DRCR', 'DRCS', 'DRCY', 'DRDA', 'DRDG', 'DRDI',
        'DRDR', 'DRDS', 'DRDT', 'DRDZ', 'DREA', 'DREB', 'DREC', 'DRED', 'DREE', 'DREF',
        'DREG', 'DREH', 'DREI', 'DREJ', 'DREK', 'DREL', 'DREM', 'DREN', 'DREO', 'DREP',
        'DREQ', 'DRER', 'DRES', 'DRET', 'DREU', 'DREV', 'DREW', 'DREX', 'DREY', 'DREZ',
        'DRFA', 'DRFB', 'DRFC', 'DRFD', 'DRFE', 'DRFF', 'DRFG', 'DRFH', 'DRFI', 'DRFJ',
        'DRFK', 'DRFL', 'DRFM', 'DRFN', 'DRFO', 'DRFP', 'DRFQ', 'DRFR', 'DRFS', 'DRFT',
        'DRFU', 'DRFV', 'DRFW', 'DRFX', 'DRFY', 'DRFZ', 'DRGA', 'DRGB', 'DRGC', 'DRGD',
        'DRGE', 'DRGF', 'DRGG', 'DRGH', 'DRGI', 'DRGJ', 'DRGK', 'DRGL', 'DRGM', 'DRGN',
        'DRGO', 'DRGP', 'DRGQ', 'DRGR', 'DRGS', 'DRGT', 'DRGU', 'DRGV', 'DRGW', 'DRGX',
        'DRGY', 'DRGZ', 'DRHA', 'DRHB', 'DRHC', 'DRHD', 'DRHE', 'DRHF', 'DRHG', 'DRHH',
        'DRHI', 'DRHJ', 'DRHK', 'DRHL', 'DRHM', 'DRHN', 'DRHO', 'DRHP', 'DRHQ', 'DRHR',
        'DRHS', 'DRHT', 'DRHU', 'DRHV', 'DRHW', 'DRHX', 'DRHY', 'DRHZ', 'DRIA', 'DRIB',
        'DRIC', 'DRID', 'DRIE', 'DRIF', 'DRIG', 'DRIH', 'DRII', 'DRIJ', 'DRIK', 'DRIL',
        'DRIM', 'DRIN', 'DRIO', 'DRIP', 'DRIQ', 'DRIR', 'DRIS', 'DRIT', 'DRIU', 'DRIV',
        'DRIW', 'DRIX', 'DRIY', 'DRIZ', 'DRJA', 'DRJB', 'DRJC', 'DRJD', 'DRJE', 'DRJF',
    ]

def download_today_prices(stocks):
    """Download today's closing prices using yfinance"""
    results = []
    total = len(stocks)
    
    print(f"\n📊 Downloading {total} stocks from IDX...")
    print("="*80)
    
    failed = []
    success_count = 0
    
    for i, stock in enumerate(stocks, 1):
        try:
            ticker = f"{stock}.JK"
            data = yf.download(ticker, period='1d', progress=False)
            
            if data.empty:
                continue
            
            latest = data.iloc[-1]
            results.append({
                'Symbol': stock,
                'Date': str(data.index[-1].date()),
                'Open': latest['Open'],
                'High': latest['High'],
                'Low': latest['Low'],
                'Close': latest['Close'],
                'Volume': int(latest['Volume']) if latest['Volume'] > 0 else 0,
                'Timestamp': datetime.now().isoformat()
            })
            
            success_count += 1
            
            # Progress indicator
            if i % 50 == 0:
                print(f"  [{i}/{total}] Downloaded {success_count} prices...")
                
        except Exception as e:
            failed.append(stock)
            continue
    
    print(f"✅ Downloaded {success_count}/{total} stocks")
    if failed:
        print(f"⚠️  Failed to fetch {len(failed)} stocks")
    
    return pd.DataFrame(results)


def main():
    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Get stock list
    stocks = get_stock_list()
    print(f"\n📈 Total stocks to process: {len(stocks)}")
    
    # Download prices
    df = download_today_prices(stocks)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved {len(df)} records to: {OUTPUT_FILE}")
    
    # Display summary
    print(f"\n📊 TODAY'S IDX CLOSING PRICES SUMMARY")
    print("="*80)
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    # Show top gainers/losers if we have previous data
    if len(df) > 0:
        print(f"\n🔝 Top 10 by Volume:")
        top_vol = df.nlargest(10, 'Volume')[['Symbol', 'Close', 'Volume']]
        for idx, row in top_vol.iterrows():
            print(f"  {row['Symbol']:<8} Rp{row['Close']:>10,.0f}  Vol: {row['Volume']:>15,}")
        
        print(f"\n💹 Latest Prices (First 10):")
        first_10 = df.head(10)[['Symbol', 'Close', 'Open', 'High', 'Low']]
        for idx, row in first_10.iterrows():
            print(f"  {row['Symbol']:<8} Close: Rp{row['Close']:>8,.0f}  H: {row['High']:>8,.0f}  L: {row['Low']:>8,.0f}")


if __name__ == '__main__':
    main()
