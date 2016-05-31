<template>
    <div>
        <div class="follw-container-body">
            <div class="body-scroll">
                <weibo-follow v-for='keyword in keywords' v-bind:key-word="keyword"></weibo-follow>
            </div>
        </div>
    </div>
</template>
<style>
    .follw-container-body {
        height: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        padding-top: 5px;
        padding-bottom: 3px;
    }

    .follw-container-body .body-scroll {
        white-space: nowrap;
        height: 100%;
    }
</style>
<script>
    import WeiboFollow from './weibo-follow.vue'
    var ws_url_base = "ws://" + location.host
    export default{
        data(){
            return {
                keywords: [],
                ws: new WebSocket(ws_url_base + "/ws/wordfollow_update/"),
                wsQueue: [],
                wsOpen: false
            }
        },
        components: {
            'weibo-follow': WeiboFollow
        },
        events: {
            'container-add-keyword': function (keyword) {
                if (this.keywords.indexOf(keyword) == -1) {
                    this.keywords.push(keyword);
                }
                this.saveKeywords();
                this.wsSend(JSON.stringify({
                    'action': 'bind',
                    'word': keyword
                }));
            },
            'container-remove-keyword': function (keyword) {
                this.keywords.$remove(keyword);
                this.saveKeywords();
                this.wsSend(JSON.stringify({
                    'action': 'unbind',
                    'word': keyword
                }));
            },
        },
        methods: {
            loadKeywords: function () {
                var default_keywords = ['江苏 高考', '南京'];
                var keywords = localStorage['weibo-follow-keywords'];
                if (keywords === undefined) {
                    keywords = default_keywords;
                }
                else {
                    try {
                        keywords = JSON.parse(keywords);
                    } catch (e) {
                        keywords = default_keywords;
                    }
                }
                this.keywords = keywords;
                for (var i = 0; i < this.keywords.length; i++) {
                    this.wsSend(JSON.stringify({
                        'action': 'bind',
                        'word': this.keywords[i]
                    }));
                }
            },
            saveKeywords: function () {
                localStorage['weibo-follow-keywords'] = JSON.stringify(this.keywords);
            },
            wordfollowUpdate: function (word, tweets) {
                this.$broadcast('wordfollow-update', word, tweets);
            },
            wsSend: function (data) {
                if (!this.wsOpen) {
                    this.wsQueue.push(data);
                }
                else {
                    this.ws.send(data);
                }
            }
        },
        route: {
            activate: function (transition) {
                this.loadKeywords();
                transition.next();
            },
            deactivate: function (transition) {
                this.saveKeywords();
                transition.next();
            }
        },
        ready: function () {
            var $this = this;
            this.ws.onmessage = function (event) {
                var data = JSON.parse(event.data);
                $this.wordfollowUpdate(data.word, data.tweets);
            }
            this.ws.onopen = function () {
                while ($this.wsQueue.length) {
                    $this.ws.send($this.wsQueue.shift());
                }
                $this.wsOpen = true;
            }
        },
        watch: {
            'keywords': function (val, oldVal) {
            }
        }
    }
</script>