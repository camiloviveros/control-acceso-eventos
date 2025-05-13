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

@register.filter
def filter_by(queryset, args):
    """
    Filtra un queryset por un atributo y un valor dados.
    Uso: queryset|filter_by:"atributo,valor"
    """
    try:
        args_list = args.split(',')
        field = args_list[0]
        value = args_list[1]
        
        # Convertir el valor según su tipo
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        
        # Crear el filtro dinámicamente
        kwargs = {field: value}
        return [item for item in queryset if getattr(item, field) == value]
    except (IndexError, AttributeError):
        return queryset