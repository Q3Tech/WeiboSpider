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
            return{
                keywords: ['江苏 高考', '南京']
            }
        },
        components:{
            'weibo-follow':WeiboFollow
        }
    }
</script>