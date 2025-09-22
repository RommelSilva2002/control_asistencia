from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from .models import Usuario

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )

class UserUpdateForm(UserChangeForm):
    password = None  # No mostrar campo de contraseña en edición
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'foto', 'facultad']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'facultad': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es admin, hacer facultad no requerida
        if self.instance and self.instance.tipo_usuario == 'admin':
            self.fields['facultad'].required = False
        else:
            self.fields['facultad'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = self.instance.tipo_usuario  # Usar el tipo del usuario actual
        facultad = cleaned_data.get('facultad')
        
        if tipo_usuario in ['docente', 'estudiante'] and not facultad:
            raise forms.ValidationError({'facultad': 'La facultad es obligatoria para docentes y estudiantes'})
        
        if tipo_usuario == 'admin':
            cleaned_data['facultad'] = None
        
        return cleaned_data