"""
Broker Classification Utility
==============================
Classify brokers as Foreign, Domestic, or State-Owned based on company names
"""

import pandas as pd

# Load broker data
brokers_df = pd.read_excel('data/reference/Broker Summary-20260120.xlsx', engine='openpyxl')

# Create classification based on company name patterns
def classify_broker(company_name):
    """Classify broker based on company name"""
    name_lower = company_name.lower()
    
    # State-owned patterns
    state_owned_keywords = ['mandiri', 'bni', 'bri', 'btn', 'bahana']
    if any(keyword in name_lower for keyword in state_owned_keywords):
        return 'State-Owned'
    
    # Foreign broker patterns
    foreign_keywords = [
        'ubs', 'morgan', 'jp morgan', 'j.p. morgan', 'goldman', 'credit suisse',
        'deutsche', 'nomura', 'dbs', 'cimb', 'uob', 'ocbc', 'maybank',
        'phillip', 'kim eng', 'kgi', 'korea investment', 'kiwoom', 'yuanta',
        'mirae', 'samsung', 'shinhan', 'hana', 'hsbc', 'standard chartered',
        'macquarie', 'clsa', 'merrill lynch', 'citigroup', 'barclays',
        'rbci', 'rbc', 'rhb', 'india', 'japan', 'china', 'hong kong',
        'singapore', 'australia', 'cgsi', 'cgs', 'commonwealth'
    ]
    
    if any(keyword in name_lower for keyword in foreign_keywords):
        return 'Foreign'
    
    # Default to domestic
    return 'Domestic'

# Apply classification
brokers_df['Broker_Type'] = brokers_df['Company Name'].apply(classify_broker)

# Display results
print("=" * 80)
print("BROKER CLASSIFICATION SUMMARY")
print("=" * 80)
print(f"\nTotal Brokers: {len(brokers_df)}")
print("\nBreakdown by Type:")
print(brokers_df['Broker_Type'].value_counts())
print()

# Show key brokers from the analysis
key_brokers = ['AK', 'CC', 'KZ', 'BB', 'LG', 'KK', 'XL', 'XC', 'DH', 'BK', 'YP']
print("\n" + "=" * 80)
print("KEY BROKERS FROM ANALYSIS")
print("=" * 80)
for code in key_brokers:
    broker_info = brokers_df[brokers_df['Company Code'] == code]
    if len(broker_info) > 0:
        name = broker_info['Company Name'].iloc[0]
        broker_type = broker_info['Broker_Type'].iloc[0]
        print(f"{code:>4} - {name:<40} [{broker_type}]")
    else:
        print(f"{code:>4} - NOT FOUND")

# Save classified broker list
output_file = 'data/reference/broker_classification.csv'
brokers_df.to_csv(output_file, index=False)
print(f"\n\nClassified broker list saved to: {output_file}")

# Show all foreign brokers
print("\n" + "=" * 80)
print("ALL FOREIGN BROKERS")
print("=" * 80)
foreign = brokers_df[brokers_df['Broker_Type'] == 'Foreign'].sort_values('Value', ascending=False)
for _, row in foreign.iterrows():
    print(f"{row['Company Code']:>4} - {row['Company Name']:<45} (Value: Rp {row['Value']/1e12:.2f}T)")

# Show all state-owned brokers
print("\n" + "=" * 80)
print("ALL STATE-OWNED BROKERS")
print("=" * 80)
state = brokers_df[brokers_df['Broker_Type'] == 'State-Owned'].sort_values('Value', ascending=False)
for _, row in state.iterrows():
    print(f"{row['Company Code']:>4} - {row['Company Name']:<45} (Value: Rp {row['Value']/1e12:.2f}T)")
