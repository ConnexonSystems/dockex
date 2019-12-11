import React from 'react';

const Welcome = React.lazy(() => import('./views/Dockex/Welcome'));
const Cluster = React.lazy(() => import('./views/Dockex/Cluster'));
const Machines = React.lazy(() => import('./views/Dockex/Machines'));
const Launch = React.lazy(() => import('./views/Dockex/Launch'));
const ProgressMonitor = React.lazy(() => import('./views/Dockex/ProgressMonitor'));

const routes = [
    { path: '/', exact: true, name: 'Home' },
    { path: '/welcome', name: 'Welcome', component: Welcome },
    { path: '/cluster', name: 'Cluster', component: Cluster },
    { path: '/machines', name: 'Machines', component: Machines },
    { path: '/launch', name: 'Launch', component: Launch },
    { path: '/experiment_progress', name: 'ProgressMonitor', component: ProgressMonitor },
];

export default routes;
