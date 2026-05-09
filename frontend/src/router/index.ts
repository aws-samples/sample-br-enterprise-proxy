import { defineRouter } from '#q-app/wrappers';
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router';
import { useAuthStore } from 'src/stores/auth';
import routes from './routes';

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory;

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  // Navigation guard for authentication
  Router.beforeEach((to, from, next) => {
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
    const requiresSuperAdmin = to.matched.some((record) => record.meta.requiresSuperAdmin);
    const accessToken = localStorage.getItem('access_token');

    if (requiresAuth && !accessToken) {
      next('/login');
    } else if (!requiresAuth && accessToken && to.path === '/login') {
      next('/');
    } else if (requiresSuperAdmin) {
      const authStore = useAuthStore();
      if (!authStore.isSuperAdmin) {
        next('/');
      } else {
        next();
      }
    } else {
      next();
    }
  });

  return Router;
});
