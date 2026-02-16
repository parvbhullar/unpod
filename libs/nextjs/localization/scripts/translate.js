const fs = require('fs');
const path = require('path');

// Translation dictionaries for each language
const translations = {
  // Spanish (es-ES)
  es: {
    // Common
    'Save': 'Guardar',
    'Cancel': 'Cancelar',
    'Delete': 'Eliminar',
    'Edit': 'Editar',
    'Create': 'Crear',
    'Update': 'Actualizar',
    'Search': 'Buscar',
    'Reset': 'Restablecer',
    'Loading...': 'Cargando...',
    'No Data': 'Sin Datos',
    'Submit': 'Enviar',
    'Back': 'Atrás',
    'Next': 'Siguiente',
    'Previous': 'Anterior',
    'Yes': 'Sí',
    'No': 'No',
    'OK': 'OK',
    'Export': 'Exportar',
    'Select region': 'Seleccionar región',
    'Change Region': 'Cambiar Región',
    'Close': 'Cerrar',
    'Confirm': 'Confirmar',
    'Success': 'Éxito',
    'Error': 'Error',
    'Warning': 'Advertencia',
    'Info': 'Info',
    'Welcome': 'Bienvenido',
    'Logout': 'Cerrar Sesión',
    'Login': 'Iniciar Sesión',
    'Sign Up': 'Registrarse',
    'Settings': 'Configuración',
    'Profile': 'Perfil',
    'Home': 'Inicio',
    'Dashboard': 'Panel',
    'Notifications': 'Notificaciones',
    'Messages': 'Mensajes',
    'Help': 'Ayuda',
    'About': 'Acerca de',
    'Contact Us': 'Contáctenos',
    'Privacy Policy': 'Política de Privacidad',
    'Terms of Service': 'Términos de Servicio',
    'Language': 'Idioma',
    'Done': 'Hecho',
    'Run': 'Ejecutar',
    'Minimize': 'Minimizar',
    'Maximize': 'Maximizar',
    'Share': 'Compartir',
    'Join': 'Unirse',
    'Subscribe': 'Suscribirse',
    'View Only': 'Solo Ver',
    'Select All': 'Seleccionar Todo',
    'Unselect All': 'Deseleccionar Todo',
    'Archive': 'Archivar',
    'Request Access': 'Solicitar Acceso',
    'Save Draft': 'Guardar Borrador',
    'Shared': 'Compartido',
    'Remove access': 'Eliminar acceso',
    'Search here...': 'Buscar aquí...',
    'No results found': 'No se encontraron resultados',
    'Save Profile': 'Guardar Perfil',
    'Save Changes': 'Guardar Cambios',
    'Update Password': 'Actualizar Contraseña',
    'Skip': 'Omitir',
    'Loading more...': 'Cargando más...',
    'Read more': 'Leer más',
    'Download': 'Descargar',
    'Pending': 'Pendiente',
    'Paid': 'Pagado',
    'Failed': 'Fallido',
    'Cancelled': 'Cancelado',
    'Refunded': 'Reembolsado',
    'Pay': 'Pagar',
    'mins': 'mins',
    'Incoming': 'Entrante',
    'Outgoing': 'Saliente',
    'No users added yet': 'No se han añadido usuarios aún',
    'Refresh': 'Actualizar',
    'Total:': 'Total:',
    'Upload': 'Subir',
    'Documentation': 'Documentación',
    'Github': 'Github',
    'Discord': 'Discord',
    'Continue': 'Continuar',
    'Choose File': 'Elegir Archivo',
    'Select': 'Seleccionar',
    'Unselect': 'Deseleccionar',
    'Upgrade': 'Actualizar',
    'Manage': 'Gestionar',
    'Add Field': 'Añadir Campo',
    'Clear': 'Limpiar',
    'Apply': 'Aplicar',
    'Created Time': 'Fecha de Creación',
    'Call': 'Llamar',
    'Need help?': '¿Necesitas ayuda?',
    'Type a message': 'Escribe un mensaje',
    'Send': 'Enviar',
    'Email': 'Correo Electrónico',
    'Password': 'Contraseña',
    'Name': 'Nombre',
    'Description': 'Descripción',
  }
};

// Function to translate text
function translateText(text, targetLang) {
  const dict = translations[targetLang];
  if (!dict) return text;
  return dict[text] || text;
}

// Read source file
const sourcePath = path.join(__dirname, '../src/locales/en_US.json');
const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));

// For now, we'll just copy the structure
// In production, you would use a translation API here
const languageMappings = {
  'ar_SA': 'ar',
  'bn_BD': 'bn',
  'es_ES': 'es',
  'fr_FR': 'fr',
  'hi_IN': 'hi',
  'ja_JP': 'ja',
  'pt_PT': 'pt',
  'ru_RU': 'ru',
  'zh_CN': 'zh'
};

// Generate translated files
Object.keys(languageMappings).forEach(locale => {
  const langCode = languageMappings[locale];
  const translated = {};

  Object.keys(source).forEach(key => {
    const value = source[key];
    translated[key] = translateText(value, langCode);
  });

  const targetPath = path.join(__dirname, `../src/locales/${locale}.json`);
  fs.writeFileSync(targetPath, JSON.stringify(translated, null, 2), 'utf8');
  console.log(`Generated ${locale}.json`);
});

console.log('Translation complete!');
