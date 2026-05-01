import { createRouter, createWebHistory } from 'vue-router';

import CampaignDashboard from '../pages/CampaignDashboard.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: CampaignDashboard,
    },
  ],
});
