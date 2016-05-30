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
    export default{
        data(){
            return {
                keywords: []
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
            },
            'container-remove-keyword': function (keyword) {
                this.keywords.$remove(keyword);
                this.saveKeywords();
            },
        },
        methods:{
            loadKeywords:function () {
                var default_keywords = ['江苏 高考', '南京'];
                var keywords = localStorage['weibo-follow-keywords'];
                if (keywords === undefined){
                    keywords = default_keywords;
                }
                else {
                    try{
                        keywords = JSON.parse(keywords);
                    }catch(e){
                        keywords = default_keywords;
                    }

                }
                this.keywords = keywords;
            },
            saveKeywords: function () {
                localStorage['weibo-follow-keywords'] = JSON.stringify(this.keywords);
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
        }
    }
</script>