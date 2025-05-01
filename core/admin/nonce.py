from django.contrib import admin
from social_django.models import Nonce, Association, UserSocialAuth, Code, Partial

# Unregister the Nonce model from the admin
admin.site.unregister(Nonce)

# Optionally, you can also unregister other social_django models if you don't need them
# Uncomment these lines if you want to hide them as well
# admin.site.unregister(Association)
# admin.site.unregister(UserSocialAuth)
# admin.site.unregister(Code)
# admin.site.unregister(Partial)
