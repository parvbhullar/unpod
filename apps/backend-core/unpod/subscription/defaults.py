SUBSCRIPTION_PLAN = [
    {'name': 'Basic', 'description': 'For businesses with advanced needs', 'price': 39, 'is_custom': True},
    {'name': 'Standard', 'description': 'For businesses with advanced needs', 'price': 39, 'is_custom': True},
    {'name': 'Advanced', 'description': 'For businesses with advanced needs', 'price': 39, 'is_custom': True}
]

PLAN_MODULES = [
    {'name': 'Videos Storage', 'unit': 'count'},
    {'name': 'Videos', 'unit': 'minute'}
]

SUBSCRIPTION_MODULES = {
    'basic': {
        'modules': {
            'Videos Storage': {'unit': 'count', 'quantity': 0},
            'Videos': {'unit': 'minute', 'quantity': 750}
        }
    },
    'standard': {
        'modules': {
            'Videos Storage': {'unit': 'count', 'quantity': 0},
            'Videos': {'unit': 'minute', 'quantity': 750}
        }
    },
    'advanced': {
        'modules': {
            'Videos Storage': {'unit': 'count', 'quantity': 0},
            'Videos': {'unit': 'minute', 'quantity': 750}
        }
    }
}



def get_table_data():
    subscription_dict = {sub['name'].lower(): sub for sub in SUBSCRIPTION_PLAN}
    subscription_plans = []

    for plan_name, plan in subscription_dict.items():
        features = []
        features.append({'title': 'Basic Features', 'value': 'Y'})
        
        for plan_module in PLAN_MODULES:
            module_name = plan_module['name']
            unit = plan_module['unit']
            quantity = 'N'
            mods = SUBSCRIPTION_MODULES.get(plan_name, {}).get('modules', {})
            mod = mods.get(module_name, {})
            mod_unit = mod.get("unit", 'N')

            if mod_unit != 'N' and mod_unit == unit:
                quantity = f"{mod.get('quantity', 'N')} {unit if unit != 'count' else ''}".strip()
            
            features.append({'title': module_name, 'value': quantity})
        features.extend([
            {'title': 'Support', 'value': 'Y'},
            {'title': 'Analytics', 'value': 'Y'},
            {'title': 'Audit Log', 'value': 'Y'}
        ])

        plan_entry = {
            'plan': plan_name,
            'title': plan['name'],
            'description': plan.get('description', 'No description available'),
            'price': float(plan.get('price', 0)),
            'is_custom': plan.get('is_custom', True),
            'features': features
        }

        subscription_plans.append(plan_entry)

    return subscription_plans





