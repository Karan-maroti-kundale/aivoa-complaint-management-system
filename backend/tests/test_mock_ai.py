from app.agents.mock_ai import mock_extract, apply_correction

def test_extract():
    r=mock_extract('Customer: Apollo Pharmacy\nProduct: Amoxicillin Capsules 500 mg\nBatch Number: AMX240602\nAffected Quantity: 48 capsules')
    assert r['customer_name']=='Apollo Pharmacy'
    assert r['batch_number']=='AMX240602'

def test_correction():
    r=apply_correction({'batch_number':'AMX240602','affected_quantity':'12 capsules'},'batch number is BMX240602 and affected quantity is 48 capsules')
    assert r['batch_number']=='BMX240602'
    assert r['affected_quantity']=='48 capsules'
