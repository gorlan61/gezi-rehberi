export default ({ env }) => ({
  upload: {
    config: {
      provider: 'cloudinary',
      providerOptions: {
        cloud_name: env('dga2sq0q4'),
        api_key: env('686263637615331'),
        api_secret: env('5OCBuDp0revvRa-lY8h-HhqjOiM'),
      },
      actionOptions: {
        upload: {},
        uploadStream: {},
        delete: {},
      },
    },
  },
});