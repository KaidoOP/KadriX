<template>
  <q-layout view="hHh lpR fFf">
    <q-header bordered class="bg-dark text-white">
      <q-toolbar>
        <q-toolbar-title>KadriX</q-toolbar-title>
        <q-badge color="accent" text-color="dark" label="Hackathon MVP" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
