
def money_convert(string):
    string = string.strip("$")
    string = string.replace(",", "")
    return string


fields = dict(
    case_filed_date = dict(
        type = 'date'
    ),
    charge_offense_date = dict(
        type = 'date'
    ),
    charge_arrest_date = dict(
        type = 'date'
    ),
    disposition_fine_costs_due = dict(
        type = 'date'
    ),
    disposition_restriction_end_date = dict(
        type = 'date'
    ),
    disposition_probation_starts = dict(
        type = 'date'
    ),
    disposition_restriction_start_date = dict(
        type = 'date'
    ),
    disposition_fine_costs_paid_date = dict(
        type = 'date'
    ),
    disposition_sentence_suspended_time = dict(
        type = 'interval'
    ),
    disposition_probation_time = dict(
        type = 'interval'
    ),
    disposition_operator_license_suspension_time = dict(
        type = 'interval'
    ),
    disposition_sentence_time = dict(
        type = 'interval'
    ),
    disposition_fine = dict(
        translator = money_convert,
        type = 'decimal'
    ),
    disposition_costs = dict(
        translator = money_convert,
        type = 'decimal'
    )
)
all_fields = """
case_status
case_name
case_locality
case_filed_date
case_gender
case_dob
case_race
case_aka1
case_address
case_case_number
case_aka2
case_defense_attorney
charge_complainant
charge_code_section
charge_amended_charge
charge_offense_date
charge_case_type
charge_charge
charge_arrest_date
charge_amended_code
charge_amended_case_type
charge_class
disposition_fine_costs_due
disposition_final_disposition
disposition_probation_type
disposition_restriction_end_date
disposition_sentence_suspended_time
disposition_operator_license_restriction_codes
disposition_probation_time
disposition_probation_starts
disposition_restriction_start_date
disposition_fine_costs_paid
disposition_costs
disposition_vasap
disposition_operator_license_suspension_time
disposition_fine
disposition_fine_costs_paid_date
disposition_sentence_time
"""

all_fields = all_fields.strip()

all_fields = all_fields.split("\n")

for field in all_fields:
    if field not in fields:
        fields[field] = dict(type = "character varying")
    else:
        if 'type' not in fields[field]:
            fields[field]['type'] = "character varying"

if __name__ == "__main__":
    import json
    for field in fields:
        print "alter table cases add column %s %s;" % (field, fields[field]['type'])
