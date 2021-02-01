import json

def merge_dict(a, b):
    def merge_aux(a, b, func):
        final = a.copy()
        for k, v in b.items():
            if k in final and isinstance(v, dict):
                final[k] = func(final[k], v, func)
            else:
                final[k] = v

        return final
    
    return merge_aux(a, b, merge_aux)
