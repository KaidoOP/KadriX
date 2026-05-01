<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-dark text-white">
      <q-toolbar>
        <q-toolbar-title class="header-title">
          <span class="brand-name">KadriX</span>
          <span class="brand-tagline">Campaign Workflow Platform</span>
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<style scoped lang="scss">
.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .brand-name {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }

  .brand-tagline {
    font-size: 11px;
    font-weight: 400;
    opacity: 0.8;
    letter-spacing: 0.3px;
  }
}

@media (max-width: 640px) {
  .header-title .brand-tagline {
    display: none;
  }
}
</style>
