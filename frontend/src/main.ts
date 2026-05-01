import '@quasar/extras/material-icons/material-icons.css';
import 'quasar/src/css/index.sass';
import './css/app.scss';

import { Quasar } from 'quasar';
import { createApp } from 'vue';

import App from './App.vue';
import { router } from './router';

createApp(App)
  .use(Quasar, {
    plugins: {},
    config: {
      brand: {
        primary: '#1f8a70',
        secondary: '#243b53',
        accent: '#d97706',
        dark: '#111827',
      },
    },
  })
  .use(router)
  .mount('#app');
