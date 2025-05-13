from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='filter_by')
def filter_by(queryset, args):
    """
    Filtra un queryset por un atributo y un valor dados.
    Uso: queryset|filter_by:"atributo,valor"
    """
    try:
        if not queryset:
            return []
            
        args_list = args.split(',')
        if len(args_list) != 2:
            return queryset
            
        field = args_list[0].strip()
        value_str = args_list[1].strip()
        
        # Convertir el valor según su tipo
        if value_str.lower() == 'true':
            value = True
        elif value_str.lower() == 'false':
            value = False
        else:
            value = value_str
        
        # Crear el filtro dinámicamente
        filtered_items = []
        for item in queryset:
            try:
                if getattr(item, field) == value:
                    filtered_items.append(item)
            except (AttributeError, TypeError):
                # Si el objeto no tiene este atributo, omitirlo
                pass
                
        return filtered_items
    except Exception as e:
        print(f"Error en filter_by: {e}")
        return queryset