/**
 * Created by Comzyh on 2016/5/29.
 */

// Vue = require('/static/js/vue.min.js');
import Vue from 'vue'
import Router from 'vue-router'
import App from './component/App.vue'
import WordFollowControl from './component/wordfollower-control.vue'
import FollowContainer from './component/follow-container.vue'
import VueAnimatedList from 'vue-animated-list'
Vue.use(VueAnimatedList)
Vue.use(Router)
var router = new Router()
router.map({
    '/wordfollow-control/': {
        component: WordFollowControl
    },
    '/': {
        component: FollowContainer
    }
})

router.start(App, '#app')
