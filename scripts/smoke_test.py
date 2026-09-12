from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.agents.mock_ai import mock_extract, apply_correction

apollo = Path(__file__).resolve().parents[1] / 'data/sample_complaints/apollo_discoloration.txt'
text = apollo.read_text(encoding='utf-8')
complaint = mock_extract(text)
assert complaint['customer_name'] == 'Apollo Pharmacy'
assert complaint['batch_number'] == 'AMX240602'
assert complaint['affected_quantity'] == '48 capsules'
assert complaint['severity'] == 'Major'
updated = apply_correction(complaint, 'batch number is BMX240602 and affected quantity is 48 capsules')
assert updated['batch_number'] == 'BMX240602'
assert updated['affected_quantity'] == '48 capsules'
print('AIVOA offline extraction/correction smoke test: PASS')
